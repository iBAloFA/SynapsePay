import json
import time
import httpx
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

class EmbeddedAgent:
    def __init__(self, proxy_url: str, channel_id: int = 101):
        self.proxy_url = proxy_url.rstrip("/")
        self.channel_id = channel_id
        self.signing_key = SigningKey.generate()
        self.pubkey_hex = self.signing_key.verify_key.encode(encoder=HexEncoder).decode("utf-8")

    def trigger_micro_payment(self, current_total: int, step: int = 20):
        new_total = current_total + step
        payload = {
            "channel_id": self.channel_id,
            "cumulative_amount": new_total,
            "timestamp": int(time.time())
        }
        canonical_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode("utf-8")
        signature = self.signing_key.sign(canonical_bytes).signature.hex()

        headers = {
            "X-Voucher-Payload": json.dumps(payload),
            "X-Voucher-Signature": signature,
            "X-Agent-Pubkey": self.pubkey_hex
        }

        try:
            httpx.post(
                f"{self.proxy_url}/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": f"Autonomous stream query #{new_total // step}"}]
                },
                headers=headers,
                timeout=5.0
            )
        except Exception:
            pass