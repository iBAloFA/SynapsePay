import base64
import json
from fastapi import FastAPI, Header, HTTPException, Request
from nacl.signing import VerifyKey
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SynapsePay Proxy Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHANNEL_STATE = {}

@app.post("/v1/chat/completions")
async def proxy_completion(request: Request, authorization: str = Header(...)):
    try:
        scheme, token_str = authorization.split(" ")
        payload_b64, sig_b64 = token_str.split(".")
        voucher_bytes = base64.b64decode(payload_b64)
        sig = base64.b64decode(sig_b64)
        voucher = json.loads(voucher_bytes.decode())
    except Exception:
        raise HTTPException(status_code=401, detail="Malformed voucher authorization header.")

    agent_pubkey_hex = voucher["agent_pubkey"]
    channel_id = voucher["channel_id"]
    cumulative_amount = voucher["cumulative_amount"]

    # Verify Ed25519 signature off-chain
    verify_key = VerifyKey(bytes.fromhex(agent_pubkey_hex))
    try:
        verify_key.verify(voucher_bytes, sig)
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid cryptographic signature on voucher.")

    prev_amount = CHANNEL_STATE.get(channel_id, {}).get("highest_amount", 0)
    if cumulative_amount < prev_amount:
        raise HTTPException(status_code=400, detail="Non-monotonic payment voucher.")

    CHANNEL_STATE[channel_id] = {
        "highest_amount": cumulative_amount,
        "latest_voucher": voucher,
        "signature_hex": sig.hex(),
        "agent": agent_pubkey_hex
    }

    # Simulate downstream tool execution
    body = await request.json()
    return {
        "id": "synapse-cmpl-1",
        "object": "chat.completion",
        "model": body.get("model", "agent-tool"),
        "choices": [{
            "message": {
                "role": "assistant",
                "content": f"Executed query: '{body.get('prompt')}'. Settled {cumulative_amount} micro-units."
            }
        }]
    }

@app.get("/channel/{channel_id}/latest")
def get_channel_voucher(channel_id: int):
    if channel_id not in CHANNEL_STATE:
        raise HTTPException(status_code=404, detail="Channel not active.")
    return CHANNEL_STATE[channel_id]

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)