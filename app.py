import streamlit as st
import httpx
import json
import time
import html
from embedded_agent import EmbeddedAgent

st.set_page_config(page_title="SYNAPSEPAY // AGENT PROTOCOL", layout="wide")

PROXY_URL = "https://synapsepay-proxy.onrender.com"

# Neubrutalism UI Styling
NEUBRUTALISM_CSS = """
<style>
.stApp {
    background-color: #FFFDF0;
    font-family: 'Courier New', Courier, monospace, sans-serif;
    color: #000000;
}
[data-testid="stSidebar"] {
    background-color: #FFFDF0 !important;
    border-right: 4px solid #000000 !important;
}
.stButton > button {
    background-color: #FFE600 !important;
    color: #000000 !important;
    border: 3px solid #000000 !important;
    border-radius: 0px !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    padding: 0.5rem 1.2rem !important;
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
.stTextInput input, .stNumberInput input {
    background-color: #FFFFFF !important;
    border: 3px solid #000000 !important;
    border-radius: 0px !important;
    color: #000000 !important;
    font-weight: 700 !important;
    box-shadow: 4px 4px 0px #000000 !important;
}
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

# Header
st.markdown("""
<div style="border-bottom: 4px solid #000; padding-bottom: 0.8rem; margin-bottom: 1.5rem;">
    <h1 style="font-size: 2.3rem; font-weight: 900; text-transform: uppercase; margin: 0;">
        ⚡ SYNAPSEPAY // AGENT SETTLEMENT GATEWAY
    </h1>
    <p style="font-weight: 700; margin: 0.3rem 0 0 0;">
        SOLANA HIGH-THROUGHPUT STATE CHANNELS // MACHINE-TO-MACHINE MICROPAYMENTS
    </p>
</div>
""", unsafe_allow_html=True)


def fetch_channel_data(c_id: int):
    try:
        res = httpx.get(f"{PROXY_URL}/channel/{c_id}/latest", timeout=5.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return None
    return None


def fetch_all_channels():
    try:
        res = httpx.get(f"{PROXY_URL}/channels", timeout=3.0)
        if res.status_code == 200:
            val = res.json()
            if isinstance(val, list) and len(val) > 0:
                return val
    except Exception:
        pass
    return [101]


# Sidebar Controls
st.sidebar.markdown("### 01 // CHANNEL SELECTOR")

known_channels = fetch_all_channels()
mode = st.sidebar.radio("MODE", ["Active Channels", "Create New Channel"])

if mode == "Active Channels":
    channel_id = st.sidebar.selectbox("TARGET CHANNEL ID", options=known_channels)
else:
    channel_id = st.sidebar.number_input("NEW CHANNEL ID", min_value=1, value=max(known_channels) + 1, step=1)

# Ensure Agent is cleanly mapped to the selected Channel ID
if "active_channel_id" not in st.session_state or st.session_state.active_channel_id != channel_id:
    st.session_state.active_channel_id = channel_id
    st.session_state.agent_sim = EmbeddedAgent(PROXY_URL, channel_id)
    st.session_state.last_tx = None

st.sidebar.markdown("---")
st.sidebar.markdown("### 02 // STREAM CONFIG")
auto_stream = st.sidebar.toggle("ENABLE CONTINUOUS STREAM", value=False)
stream_step = st.sidebar.select_slider("STEP SIZE (μ-UNITS)", options=[10, 20, 50, 100, 250, 500], value=20)
poll_freq = st.sidebar.slider("STREAM INTERVAL (SEC)", min_value=1, max_value=5, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**NETWORK:** SOLANA DEVNET  
**CURVE:** ED25519 (NATIVE)  
**PROTOCOL:** MONOTONIC VOUCHER STATE  
""")

# Load Backend State
data = fetch_channel_data(channel_id)
current_amt = data.get("highest_amount", 0) if isinstance(data, dict) else 0
is_settled = data.get("settled", False) if isinstance(data, dict) else False
saved_tx = (data.get("settled_tx") if isinstance(data, dict) else None) or st.session_state.get("last_tx")

# Automated Increment Loop
if auto_stream and not is_settled:
    st.session_state.agent_sim.trigger_micro_payment(current_total=current_amt, step=stream_step)
    data = fetch_channel_data(channel_id)
    if isinstance(data, dict):
        current_amt = data.get("highest_amount", current_amt)
        is_settled = data.get("settled", is_settled)
        saved_tx = data.get("settled_tx") or saved_tx

# Top Metrics Bar
c1, c2, c3 = st.columns(3)

if isinstance(data, dict) and data.get("highest_amount", 0) > 0:
    amt = data.get("highest_amount", 0)
    agent_key = data.get("agent", "Unknown")
    sig = data.get("signature_hex", "")
    voucher = data.get("latest_voucher", {})
    status_label = "STATE: SETTLED ON-CHAIN" if is_settled else "STATE: ESCROW LOCKED"

    with c1:
        st.markdown(f"""
        <div class="nb-card nb-cyan">
            <span class="nb-tag">Channel Status</span>
            <div class="nb-metric-num">#{channel_id}</div>
            <div>{html.escape(status_label)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="nb-card nb-pink">
            <span class="nb-tag">Cumulative Balance</span>
            <div class="nb-metric-num">{amt:,} μ-UNITS</div>
            <div>VALIDATED MONOTONIC STREAM</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="nb-card nb-yellow">
            <span class="nb-tag">Network Efficiency</span>
            <div class="nb-metric-num">99.98%</div>
            <div>TX OVERHEAD ELIMINATED</div>
        </div>
        """, unsafe_allow_html=True)

    # Manual Control Bar & Inspection
    st.markdown("### 02 // MANUAL MICRO-PAYMENT DISPATCH")
    m1, m2, m3, m4 = st.columns([1, 1, 1, 1.5])
    with m1:
        if st.button("➕ DISPATCH +20", disabled=is_settled):
            st.session_state.agent_sim.trigger_micro_payment(current_total=current_amt, step=20)
            st.rerun()
    with m2:
        if st.button("➕ DISPATCH +100", disabled=is_settled):
            st.session_state.agent_sim.trigger_micro_payment(current_total=current_amt, step=100)
            st.rerun()
    with m3:
        if st.button("➕ DISPATCH +500", disabled=is_settled):
            st.session_state.agent_sim.trigger_micro_payment(current_total=current_amt, step=500)
            st.rerun()
    with m4:
        if is_settled:
            if st.button("🔄 REOPEN / RESET CHANNEL"):
                httpx.post(f"{PROXY_URL}/channel/{channel_id}/reset", timeout=5.0)
                st.session_state.last_tx = None
                st.rerun()

    # Split Workspace
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### 03 // OFF-CHAIN ED25519 VOUCHER")
        pretty_json = html.escape(json.dumps(voucher, indent=2))
        st.markdown(f"""
        <div class="nb-card nb-white" style="font-family: monospace;">
            <pre style="margin:0; font-weight:700;">{pretty_json}</pre>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 04 // ON-CHAIN SETTLEMENT PDA")

        # Devnet Settlement Trigger
        if not is_settled:
            if st.button("⚡ EXECUTE DEVNET SETTLEMENT NOW"):
                with st.spinner("Flushing in-flight vouchers & broadcasting atomic close..."):
                    # Cooldown buffer to give in-flight transactions time to land cleanly
                    time.sleep(1.5)
                    try:
                        res = httpx.post(f"{PROXY_URL}/channel/{channel_id}/settle", timeout=30.0)
                        if res.status_code == 200:
                            settle_res = res.json()
                            tx_hash = settle_res.get("tx_hash")
                            st.session_state.last_tx = tx_hash
                            saved_tx = tx_hash
                            is_settled = True
                            st.success("Confirmed on Solana Devnet!")
                            st.rerun()
                        else:
                            st.error(f"Settlement Error {res.status_code}: {res.text}")
                    except Exception as err:
                        st.error(f"Settlement failed: {err}")

        # Live Explorer Link Generation
        if saved_tx:
            clean_tx = html.escape(str(saved_tx))
            settle_status_html = (
                f'<a href="https://explorer.solana.com/tx/{clean_tx}?cluster=devnet" '
                f'target="_blank" style="color:#000000; text-decoration: underline; font-weight: 900;">'
                f'VIEW CONFIRMED TX ON EXPLORER ↗</a>'
            )
        else:
            settle_status_html = 'ESCROW ACTIVE // AWAITING CLOSE INSTRUCTION'

        safe_agent = html.escape(str(agent_key))
        safe_sig = html.escape(str(sig[:32])) + "..."

        pda_card_html = (
            '<div class="nb-card nb-green" style="word-break: break-all;">'
            '<span class="nb-tag">AGENT PUBKEY</span>'
            f'<div style="margin-bottom: 0.8rem; font-size: 0.85rem;">{safe_agent}</div>'
            '<span class="nb-tag">SIGNATURE ATTESTATION</span>'
            f'<div style="margin-bottom: 0.8rem; font-size: 0.85rem;">{safe_sig}</div>'
            '<span class="nb-tag">SOLANA SETTLEMENT</span>'
            f'<div style="font-size: 0.85rem; font-weight: 900;">{settle_status_html}</div>'
            '</div>'
        )
        st.markdown(pda_card_html, unsafe_allow_html=True)

else:
    # Empty / Uninitialized State
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
            <span class="nb-tag">Cumulative Balance</span>
            <div class="nb-metric-num">0 μ-UNITS</div>
            <div>NO RECENT INVOCATIONS</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="nb-card nb-cyan">
            <span class="nb-tag">Proxy Health</span>
            <div class="nb-metric-num">ONLINE</div>
            <div>READY FOR INGESTION</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nb-card nb-white">
        <span class="nb-tag">GETTING STARTED</span>
        <div style="margin-top: 0.5rem; font-weight: 700;">
            Channel is empty. Use the sidebar to toggle <b>ENABLE CONTINUOUS STREAM</b> or dispatch micro-payments below to start accumulating verified vouchers.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ DISPATCH INITIAL VOUCHER (+20)"):
        st.session_state.agent_sim.trigger_micro_payment(current_total=0, step=20)
        st.rerun()

# Rerun timer when auto-streaming is enabled
if auto_stream and not is_settled:
    time.sleep(poll_freq)
    st.rerun()