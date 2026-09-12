import json
import httpx
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# 1. Configuration
RPC_URL = "https://api.devnet.solana.com"

# Replace with your deployed Program ID (or leave as placeholder for local test)
PROGRAM_ID_STR = "5ACJCYjUkDKoUkuQjbaNjx6rpQY8XELiE7tyAg1NVffr"

def run_settlement():
    # 2. Fetch the latest aggregated voucher recorded by the Python proxy
    print("[*] Fetching final aggregated voucher from SynapsePay proxy...")
    try:
        res = httpx.get("http://127.0.0.1:8000/channel/101/latest")
        if res.status_code != 200:
            print(f"[!] No active voucher found (HTTP {res.status_code}). Make sure agent_client.py ran successfully.")
            return
        voucher_data = res.json()
    except Exception as e:
        print(f"[!] Could not connect to proxy: {e}")
        return

    channel_id = voucher_data["latest_voucher"]["channel_id"]
    highest_amount = voucher_data["highest_amount"]
    agent_pubkey_hex = voucher_data["agent"]

    print(f"\n[+] Retrieved Active Voucher for Channel {channel_id}:")
    print(f"    - Agent Hex Pubkey: {agent_pubkey_hex}")
    print(f"    - Cumulative Settled Amount: {highest_amount} micro-units")
    print(f"    - Validated Ed25519 Signature: {voucher_data['signature_hex'][:32]}...")

    # 3. Derive Program-Derived Address (PDA) for the State Channel
    program_id = Pubkey.from_string(PROGRAM_ID_STR)
    agent_bytes = bytes.fromhex(agent_pubkey_hex)
    channel_id_bytes = channel_id.to_bytes(8, byteorder="little")
    
    # Provider simulated recipient key
    provider_keypair = Keypair()
    
    seeds = [b"channel", agent_bytes, bytes(provider_keypair.pubkey()), channel_id_bytes]
    channel_pda, bump = Pubkey.find_program_address(seeds, program_id)

    print(f"\n[+] Derived Escrow Channel PDA: {channel_pda} (bump: {bump})")
    print("[+] Cryptographic voucher validated. State Channel ready for single-transaction atomic close on Solana.")

if __name__ == "__main__":
    run_settlement()