# SynapsePay ⚡
**Sub-cent State Channel Micropayment Gateway for Autonomous AI Agents on Solana**

SynapsePay is a unidirectional, state-channel micropayment proxy tailored for autonomous machine-to-machine (M2M) micro-commerce. It allows autonomous agents to stream sub-cent micro-authorizations per LLM token or API call off-chain, backed by a Solana Anchor escrow program with single-transaction atomic batch settlement.

---

## 💡 The Problem
Autonomous AI agents are bottlenecked by legacy Web2 and current Web3 payment rails:
* **Web2 Bottleneck:** Agents cannot obtain credit cards, complete KYC verification (Stripe/banks), or manage monthly subscription tiers.
* **Web3 Latency & Gas Overhead:** Submitting an on-chain transaction for every API call, search query, or LLM token completion causes latency spikes (~400ms+) and accumulates prohibitive network fees.

## 🚀 The Solution
SynapsePay separates continuous API authorization from final financial settlement:
1. **Escrow Lock:** The agent initializes an escrow channel on Solana, depositing an SPL token budget into a Program-Derived Address (PDA).
2. **Off-Chain Streaming:** The agent attaches an Ed25519 cryptographic voucher (`channel_id`, `cumulative_amount`, `nonce`) to each HTTP request header.
3. **Low-Latency Verification:** The proxy validates the signature off-chain in sub-milliseconds, checks balance monotonicity, and forwards the prompt to upstream LLM/tool providers.
4. **Single-Transaction Settle:** When the session concludes, the provider submits the highest counter-signed voucher to the Solana contract, executing an Ed25519 instruction introspection check to pay the provider and refund any remaining balance atomically.

---

## 🏛️ System Architecture

```text
[ AI Agent Client ]
        │  (1) Locks SPL Escrow on Solana Devnet
        ▼
[ Solana Anchor Program ] <── Program-Derived Address (PDA)
        │
        │  (2) Streams HTTP + Signed Ed25519 Micro-Vouchers
        ▼
[ SynapsePay Proxy Gateway ] ── (3) Off-chain Sig Verify & Forward to AI Model
        │
        │  (4) Submits Highest Counter-Signed Voucher
        ▼
[ Solana Anchor Program ] ── Atomic Close: Transfers Provider Pay + Refunds Agent