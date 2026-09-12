import os
import json
import base64
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction

app = FastAPI(title="SynapsePay Proxy Gateway")

# Enable CORS for Streamlit Cloud
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unified global state
CHANNEL_STATE = {}

# Solana Devnet Client Setup
SOLANA_RPC = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
solana_client = Client(SOLANA_RPC)


def get_payer_keypair() -> Keypair:
    raw_key = os.getenv("SETTLEMENT_PRIVATE_KEY")
    if not raw_key:
        raise ValueError("SETTLEMENT_PRIVATE_KEY environment variable is missing on Render.")
    
    # Clean up formatting in case it was pasted with whitespace or quotes
    raw_key = raw_key.strip().strip("'").strip('"')
    key_bytes = bytes(json.loads(raw_key))
    return Keypair.from_bytes(key_bytes)


@app.get("/")
def root():
    return {"status": "online", "service": "SynapsePay State Channel Proxy"}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


@app.post("/v1/chat/completions")
async def proxy_completion(request: Request):
    auth_header = request.headers.get("authorization")
    x_payload = request.headers.get("x-voucher-payload")
    x_sig = request.headers.get("x-voucher-signature")
    x_pubkey = request.headers.get("x-agent-pubkey")

    try:
        if auth_header and " " in auth_header:
            scheme, token = auth_header.split(" ", 1)
            sig_b64, voucher_b64 = token.split(".", 1)
            voucher_bytes = base64.b64decode(voucher_b64)
            sig_bytes = base64.b64decode(sig_b64)
            voucher = json.loads(voucher_bytes.decode("utf-8"))
            agent_pubkey_hex = voucher["agent_pubkey"]
        elif x_payload and x_sig and x_pubkey:
            voucher = json.loads(x_payload)
            voucher_bytes = json.dumps(voucher, sort_keys=True, separators=(',', ':')).encode("utf-8")
            sig_bytes = bytes.fromhex(x_sig)
            agent_pubkey_hex = x_pubkey
        else:
            raise HTTPException(status_code=401, detail="Malformed voucher authorization headers")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail="Malformed voucher authorization format")

    channel_id = voucher.get("channel_id", 101)
    cumulative_amount = voucher.get("cumulative_amount", 0)

    # 2. Verify Ed25519 signature off-chain
    try:
        vk_bytes = bytes.fromhex(agent_pubkey_hex) if len(agent_pubkey_hex) == 64 else base64.b64decode(agent_pubkey_hex)
        verify_key = VerifyKey(vk_bytes)
        verify_key.verify(voucher_bytes, sig_bytes)
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid cryptographic signature on voucher")

    # 3. Monotonic amount validation
    prev_state = CHANNEL_STATE.get(channel_id, {"highest_amount": 0})
    if cumulative_amount < prev_state["highest_amount"]:
        raise HTTPException(status_code=400, detail="Non-monotonic payment voucher")

    # 4. Store updated state
    sig_hex = sig_bytes.hex()
    CHANNEL_STATE[channel_id] = {
        "channel_id": channel_id,
        "highest_amount": cumulative_amount,
        "signature_hex": sig_hex,
        "agent": agent_pubkey_hex,
        "latest_voucher": voucher
    }

    return {
        "id": f"synapse-{int(os.times().system)}",
        "object": "chat.completion",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": f"Executed query: Settled [{cumulative_amount}] micro-units."
            }
        }]
    }


@app.get("/channel/{channel_id}/latest")
def get_latest_channel_state(channel_id: int):
    if channel_id not in CHANNEL_STATE:
        return {
            "channel_id": channel_id,
            "highest_amount": 0,
            "agent": "Awaiting first voucher",
            "signature_hex": "0" * 64,
            "latest_voucher": {
                "channel_id": channel_id,
                "cumulative_amount": 0,
                "status": "initialized"
            }
        }
    return CHANNEL_STATE[channel_id]


# Supports both POST (from Streamlit button) and GET requests without 405 errors
@app.api_route("/channel/{channel_id}/settle", methods=["GET", "POST"])
def trigger_settle_endpoint(channel_id: int):
    state = CHANNEL_STATE.get(channel_id)
    if not state or state.get("highest_amount", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Channel #{channel_id} has no active vouchers to settle."
        )

    try:
        # Load your SolPG fee-payer wallet from Render environment variables
        payer = get_payer_keypair()
        cumulative_units = state["highest_amount"]

        # Convert micro-units to lamports (1 lamport = 1 micro-unit, minimum dust floor)
        settle_lamports = max(int(cumulative_units), 1000)

        # Get recent blockhash from Solana Devnet
        blockhash_resp = solana_client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash

        # Transfer instruction executed on-chain to confirm settlement
        ix = transfer(
            TransferParams(
                from_pubkey=payer.pubkey(),
                to_pubkey=payer.pubkey(),
                lamports=settle_lamports
            )
        )

        tx = Transaction.new_signed_with_payer(
            [ix],
            payer.pubkey(),
            [payer],
            recent_blockhash
        )

        # Send transaction directly to the Solana Devnet cluster
        result = solana_client.send_transaction(tx)
        tx_hash = str(result.value)

        # Update in-memory state
        state["settled"] = True
        state["settled_tx"] = tx_hash

        return {
            "status": "success",
            "channel_id": channel_id,
            "settled_amount": cumulative_units,
            "tx_hash": tx_hash
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"On-chain settlement failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("proxy:app", host="0.0.0.0", port=port, reload=False)