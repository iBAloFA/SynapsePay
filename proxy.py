import os
import json
import base64
import time
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nacl.signing import VerifyKey
from solders.keypair import Keypair
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solders.transaction import Transaction
from solders.hash import Hash

app = FastAPI(title="SynapsePay Proxy Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory channel store (maps channel_id -> channel ledger)
CHANNEL_STATE = {}
SOLANA_RPC = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")


def get_payer_keypair() -> Keypair:
    raw_key = os.getenv("SETTLEMENT_PRIVATE_KEY")
    if not raw_key:
        raise ValueError("SETTLEMENT_PRIVATE_KEY environment variable is missing.")
    raw_key = raw_key.strip().strip("'").strip('"')
    return Keypair.from_bytes(bytes(json.loads(raw_key)))


def solana_rpc_call(method: str, params: list):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    resp = httpx.post(SOLANA_RPC, json=payload, timeout=25.0)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Solana RPC Error: {data['error']}")
    return data["result"]


@app.get("/")
def root():
    return {"status": "online", "service": "SynapsePay State Channel Proxy"}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


@app.get("/channels")
def list_active_channels():
    # Return all active/known channels. Defaults to [101] if none yet registered
    return sorted(list(CHANNEL_STATE.keys())) if CHANNEL_STATE else [101]


@app.post("/channel/{channel_id}/reset")
def reset_channel(channel_id: int):
    # Cleanses state to allow opening a fresh cycle on the same ID
    CHANNEL_STATE[channel_id] = {
        "channel_id": channel_id,
        "highest_amount": 0,
        "agent": "Awaiting first voucher",
        "signature_hex": "0" * 64,
        "settled": False,
        "settled_tx": None,
        "latest_voucher": {
            "channel_id": channel_id,
            "cumulative_amount": 0,
            "status": "ready"
        }
    }
    return {"status": "reset", "channel_id": channel_id}


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
            voucher_bytes = json.dumps(voucher, sort_keys=True, separators=(",", ":")).encode("utf-8")
            sig_bytes = bytes.fromhex(x_sig)
            agent_pubkey_hex = x_pubkey
        else:
            raise HTTPException(status_code=401, detail="Malformed voucher authorization headers")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail="Malformed voucher authorization format")

    channel_id = int(voucher.get("channel_id", 101))
    cumulative_amount = int(voucher.get("cumulative_amount", 0))

    # Cryptographic Ed25519 verification
    try:
        vk_bytes = bytes.fromhex(agent_pubkey_hex) if len(agent_pubkey_hex) == 64 else base64.b64decode(agent_pubkey_hex)
        verify_key = VerifyKey(vk_bytes)
        verify_key.verify(voucher_bytes, sig_bytes)
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid cryptographic signature on voucher")

    prev_state = CHANNEL_STATE.get(channel_id, {"highest_amount": 0, "settled": False, "settled_tx": None})
    
    # Disallow streaming into an already settled channel until reset
    if prev_state.get("settled", False):
        raise HTTPException(status_code=400, detail=f"Channel #{channel_id} has been settled on-chain. Reset channel to reopen.")

    # Enforce monotonic constraint
    if cumulative_amount < prev_state["highest_amount"]:
        raise HTTPException(status_code=400, detail="Non-monotonic payment voucher")

    CHANNEL_STATE[channel_id] = {
        "channel_id": channel_id,
        "highest_amount": cumulative_amount,
        "signature_hex": sig_bytes.hex(),
        "agent": agent_pubkey_hex,
        "latest_voucher": voucher,
        "settled": False,
        "settled_tx": None,
        "updated_at": time.time()
    }

    return {
        "id": f"synapse-{int(time.time())}",
        "object": "chat.completion",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": f"Executed query: Settled [{cumulative_amount}] micro-units.",
                }
            }
        ],
    }


@app.get("/channel/{channel_id}/latest")
def get_latest_channel_state(channel_id: int):
    if channel_id not in CHANNEL_STATE:
        return {
            "channel_id": channel_id,
            "highest_amount": 0,
            "agent": "Awaiting first voucher",
            "signature_hex": "0" * 64,
            "settled": False,
            "settled_tx": None,
            "latest_voucher": {
                "channel_id": channel_id,
                "cumulative_amount": 0,
                "status": "initialized",
            },
        }
    return CHANNEL_STATE[channel_id]


@app.api_route("/channel/{channel_id}/settle", methods=["GET", "POST"])
def trigger_settle_endpoint(channel_id: int):
    state = CHANNEL_STATE.get(channel_id)
    if not state or state.get("highest_amount", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Channel #{channel_id} has no active vouchers to settle.",
        )

    if state.get("settled", False) and state.get("settled_tx"):
        return {
            "status": "already_settled",
            "channel_id": channel_id,
            "settled_amount": state["highest_amount"],
            "tx_hash": state["settled_tx"],
        }

    try:
        payer = get_payer_keypair()
        cumulative_units = state["highest_amount"]
        # Convert micro-units to lamports (1 unit = 100 lamports for demo pacing)
        settle_lamports = max(int(cumulative_units * 100), 5000)

        # 1. Fetch fresh blockhash with confirmed commitment
        blockhash_info = solana_rpc_call(
            "getLatestBlockhash", 
            [{"commitment": "confirmed"}]
        )
        recent_blockhash = Hash.from_string(blockhash_info["value"]["blockhash"])

        # 2. Build on-chain transfer instruction
        ix = transfer(
            TransferParams(
                from_pubkey=payer.pubkey(),
                to_pubkey=payer.pubkey(),
                lamports=settle_lamports,
            )
        )

        # 3. Construct and sign
        msg = Message([ix], payer.pubkey())
        tx = Transaction([payer], msg, recent_blockhash)

        # 4. Broadcast with preflight verification
        tx_bytes = bytes(tx)
        tx_b64 = base64.b64encode(tx_bytes).decode("utf-8")
        real_tx_sig = solana_rpc_call(
            "sendTransaction",
            [
                tx_b64,
                {
                    "encoding": "base64",
                    "skipPreflight": False,
                    "preflightCommitment": "confirmed",
                },
            ],
        )

        # 5. Await block inclusion
        for _ in range(15):
            time.sleep(1)
            status_resp = solana_rpc_call(
                "getSignatureStatuses",
                [[real_tx_sig], {"searchTransactionHistory": True}],
            )
            statuses = status_resp.get("value", [])
            if statuses and statuses[0] is not None:
                status = statuses[0]
                if status.get("err"):
                    raise RuntimeError(f"Solana transaction failed on-chain: {status['err']}")
                if status.get("confirmationStatus") in ("confirmed", "finalized"):
                    break

        state["settled"] = True
        state["settled_tx"] = str(real_tx_sig)

        return {
            "status": "success",
            "channel_id": channel_id,
            "settled_amount": cumulative_units,
            "tx_hash": str(real_tx_sig),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"On-chain settlement failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("proxy:app", host="0.0.0.0", port=port, reload=False)