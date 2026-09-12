import base64
import json
import time
from nacl.signing import SigningKey
import httpx

class SynapseAgentClient:
    def __init__(self, channel_id: int, proxy_url: str = "http://127.0.0.1:8000"):
        # Generate or load an Ed25519 signing keypair for the agent
        self.signing_key = SigningKey.generate()
        self.verify_key = self.signing_key.verify_key
        self.channel_id = channel_id
        self.proxy_url = proxy_url
        self.cumulative_spent = 0

    def sign_voucher(self, cost: int) -> str:
        self.cumulative_spent += cost
        payload = {
            "channel_id": self.channel_id,
            "agent_pubkey": self.verify_key.encode().hex(),
            "cumulative_amount": self.cumulative_spent,
            "timestamp": int(time.time()),
        }
        voucher_bytes = json.dumps(payload, separators=(',', ':')).encode()
        signature = self.signing_key.sign(voucher_bytes).signature

        p_b64 = base64.b64encode(voucher_bytes).decode()
        s_b64 = base64.b64encode(signature).decode()
        return f"Bearer {p_b64}.{s_b64}"

    def query(self, prompt: str, cost: int = 15):
        voucher_auth = self.sign_voucher(cost)
        with httpx.Client() as client:
            res = client.post(
                f"{self.proxy_url}/v1/chat/completions",
                headers={"Authorization": voucher_auth},
                json={"prompt": prompt, "model": "gpt-4o-agentic-tool"}
            )
            if res.status_code != 200:
                print(f"[!] Request failed with HTTP {res.status_code}: {res.text}")
                return None
            return res.json()

if __name__ == "__main__":
    print("--- Simulating Autonomous Agent Micropayments ---")
    agent = SynapseAgentClient(channel_id=101)

    queries = [
        "Find arbitrage routes between Raydium and Orca",
        "Fetch latest oracle price for SOL/USD",
        "Execute flash hedge on lending pool"
    ]

    for i, q in enumerate(queries, 1):
        print(f"\n[Agent -> Proxy] Query #{i}: {q}")
        response = agent.query(q, cost=20)
        if response and 'choices' in response:
            print(f"[Proxy -> Agent] Result: {response['choices'][0]['message']['content']}")
        else:
            print("[Proxy -> Agent] Request failed, aborting next steps.")

    # Check the aggregated voucher state recorded by proxy
    with httpx.Client() as client:
        res = client.get("http://127.0.0.1:8000/channel/101/latest")
        if res.status_code == 200:
            print("\n=== Aggregated Voucher Ready for Solana Settlement ===")
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"\n[!] Could not fetch channel state: {res.text}")
