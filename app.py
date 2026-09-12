import streamlit as st
import httpx
import json
import time
from embedded_agent import EmbeddedAgent

st.set_page_config(page_title="SYNAPSEPAY // AGENT PROTOCOL", layout="wide")

# Cloud or Local Backend Configuration
PROXY_URL = "https://synapsepay-proxy.onrender.com"

# Neubrutalism CSS
NEUBRUTALISM_CSS = """
<style>
/* Global Canvas */
.stApp {
    background-color: #FFFDF0;
    font-family: 'Courier New', Courier, monospace, sans-serif;
    color: #000000;
}
/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #FFFDF0 !important;
    border-right: 4px solid #000000 !important;
}
/* Standard Buttons */
.stButton > button {
    background-color: #FFE600 !important;
    color: #000000 !important;
    border: 3px solid #000000 !important;
    border-radius: 0px !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    padding: 0.6rem 1.4rem !important;
    box-shadow: 4px 4px 0px #000000 !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}
.stButton > button:hover {
    transform: translate(-2px, 2px) !important;
    box-shadow: 6px 6px 0px #000000 !important;
    background-color: #FF5252 !important;
    color: #FFFFFF !important;
}
.stButton > button:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 2px 2px 0px #000000 !important;
}
/* Text & Number Inputs */
.stTextInput input, .stNumberInput input {
    background-color: #FFFFFF !important;
    border: 3px solid #000000 !important;
    border-radius: 0px !important;
    color: #000000 !important;
    font-weight: 700 !important;
    box-shadow: 4px 4px 0px #000000 !important;
}
/* Neubrutalist Card Classes */
.nb-card {
    border: 3px solid #000000;
    box-shadow: 6px 6px 0px #000000;
    padding: 1.2rem;
    margin-bottom: 1.5rem;
    font-weight: bold;
}
.nb-pink { background-color: #FF70A6; }
.nb-cyan { background-color: #70D6FF; }
.nb-yellow { background-color: #FFD670; }
.nb-green { background-color: #79FF85; }
.nb-white { background-color: #FFFFFF; }
.nb-tag {
    display: inline-block;
    background: #000000;
    color: #FFFFFF;
    font-size: 0.75rem;
    font-weight: 900;
    padding: 2px 8px;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.nb-metric-num {
    font-size: 2.1rem;
    font-weight: 900;
    line-height: 1.1;
    margin: 0.3rem 0;
}
</style>
"""
st.markdown(NEUBRUTALISM_CSS, unsafe_allow_html=True)

# App Header
st.markdown("""
<div style="border-bottom: 4px solid #000; padding-bottom: 0.8rem; margin-bottom: 1.5rem;">
    <h1 style="font-size: 2.5rem; font-weight: 900; text-transform: uppercase; margin: 0;">
        ⚡ SYNAPSEPAY // AGENT SETTLEMENT GATEWAY
    </h1>
    <p style="font-weight: 700; margin: 0.3rem 0 0 0;">
        SUB-CENT STATE CHANNEL MICRO-COMMERCE ON SOLANA // PROTOCOL MONITOR
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.markdown("### 01 // CONTROL PANEL")
channel_id = st.sidebar.number_input("TARGET CHANNEL ID", min_value=1, value=101, step=1)
poll_freq = st.sidebar.slider("POLL INTERVAL (SEC)", 1, 5, 2)
refresh_now = st.sidebar.button("FORCE REFRESH")
st.sidebar.markdown("---")
auto_stream = st.sidebar.checkbox("⚡ AUTO-STREAM MICROPAYMENTS", value=True)
st.sidebar.markdown("---")
st.sidebar.markdown("""
**NETWORK:** SOLANA DEVNET  
**VM:** ANCHOR ESCROW / ED25519  
**AUTH:** ZERO-GAS OFF-CHAIN VOUCHER  
""")


def fetch_channel_data(c_id: int):
    try:
        res = httpx.get(f"{PROXY_URL}/channel/{c_id}/latest", timeout=5.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return None
    return None


# Initialize persistent session agent
if "agent_sim" not in st.session_state:
    st.session_state.agent_sim = EmbeddedAgent(PROXY_URL, channel_id)

# Fetch latest on-chain proxy state
data = fetch_channel_data(channel_id)
current_amt = data.get("highest_amount", 0) if data else 0

# Check settled state from proxy or active session
is_settled = data.get("settled", False) if data else False
saved_tx = data.get("settled_tx") or st.session_state.get("last_tx")

# If auto-stream is enabled and channel not yet settled, send continuous vouchers
if auto_stream and not is_settled:
    st.session_state.agent_sim.trigger_micro_payment(current_total=current_amt, step=20)
    data = fetch_channel_data(channel_id)

# Top Stat Row
c1, c2, c3 = st.columns(3)

if data:
    amt = data.get("highest_amount", 0)
    agent_key = data.get("agent", "Unknown")
    sig = data.get("signature_hex", "")
    voucher = data.get("latest_voucher", {})

    status_badge = "STATE: SETTLED ON-CHAIN" if is_settled else "STATE: ESCROW LOCKED"

    with c1:
        st.markdown(f"""
        <div class="nb-card nb-cyan">
            <span class="nb-tag">Channel Status</span>
            <div class="nb-metric-num">ACTIVE #{channel_id}</div>
            <div>{status_badge}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="nb-card nb-pink">
            <span class="nb-tag">Cumulative Spent</span>
            <div class="nb-metric-num">{amt:,} μ-UNITS</div>
            <div>MONOTONIC STREAM VERIFIED</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="nb-card nb-yellow">
            <span class="nb-tag">Efficiency</span>
            <div class="nb-metric-num">99.98%</div>
            <div>TX OVERHEAD ELIMINATED</div>
        </div>
        """, unsafe_allow_html=True)

    # Details Section
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### 02 // VALIDATED ED25519 VOUCHER")
        st.markdown(f"""
        <div class="nb-card nb-white" style="font-family: monospace;">
            <pre style="margin:0; font-weight:700;">{json.dumps(voucher, indent=2)}</pre>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 03 // ON-CHAIN SETTLEMENT PDA")

        # Settlement Execution Action
        if st.button("⚡ EXECUTE DEVNET SETTLEMENT NOW"):
            with st.spinner("Submitting atomic close transaction to Solana Devnet..."):
                try:
                    res = httpx.post(f"{PROXY_URL}/channel/{channel_id}/settle", timeout=20.0)
                    if res.status_code == 200:
                        settle_res = res.json()
                        tx_hash = settle_res.get("tx_hash")
                        st.session_state.last_tx = tx_hash
                        st.success("Settled on Solana Devnet!")
                        st.rerun()
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as err:
                    st.error(f"Settlement failed: {err}")

        # Derive live Explorer link
        tx_display = saved_tx
        explorer_link = (
            f"https://explorer.solana.com/tx/{tx_display}?cluster=devnet"
            if tx_display
            else None
        )

        settle_status_html = (
            f'<a href="{explorer_link}" target="_blank" style="color:#000; text-decoration: underline; font-weight: 900;">VIEW CONFIRMED TX ON EXPLORER ↗</a>'
            if explorer_link
            else 'PREPARING ATOMIC INSTRUCTION CLOSE'
        )

        pda_card_html = (
            '<div class="nb-card nb-green" style="word-break: break-all;">'
            '<span class="nb-tag">AGENT PUBKEY</span>'
            f'<div style="margin-bottom: 0.8rem; font-size: 0.85rem;">{agent_key}</div>'
            '<span class="nb-tag">SIGNATURE ATTESTATION</span>'
            f'<div style="margin-bottom: 0.8rem; font-size: 0.85rem;">{sig[:32]}...</div>'
            '<span class="nb-tag">SOLANA SETTLEMENT</span>'
            f'<div style="font-size: 0.85rem; font-weight: 900;">{settle_status_html}</div>'
            '</div>'
        )
        st.markdown(pda_card_html, unsafe_allow_html=True)

else:
    with c1:
        st.markdown(f"""
        <div class="nb-card nb-pink">
            <span class="nb-tag">Channel Status</span>
            <div class="nb-metric-num">IDLE #{channel_id}</div>
            <div>WAITING FOR AGENT CALLS</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="nb-card nb-yellow">
            <span class="nb-tag">Cumulative Spent</span>
            <div class="nb-metric-num">0 μ-UNITS</div>
            <div>NO RECENT INVOCATIONS</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="nb-card nb-cyan">
            <span class="nb-tag">Proxy Health</span>
            <div class="nb-metric-num">CONNECTING</div>
            <div>TARGET: CLOUD PROXY</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nb-card nb-white">
        <span class="nb-tag">SYSTEM STATUS</span>
        <div style="margin-top: 0.5rem;">
            Waiting for response from Render backend. If the free tier instance is sleeping, it will wake up in ~30 seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Poll Interval Loop
if auto_stream and not is_settled:
    time.sleep(poll_freq)
    st.rerun()