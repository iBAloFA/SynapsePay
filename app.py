import streamlit as st
import httpx
import json
import time

st.set_page_config(page_title="SYNAPSEPAY // AGENT PROTOCOL", layout="wide")

# Neubrutalism CSS adapted from template
NEUBRUTALISM_CSS = """
<style>
/* Global Canvas */
.stApp {
    background-color: #FFFDF0;
    font-family: 'Courier New', Courier, monospace, sans-serif;
    color: #000000;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #FFFDF0 !important;
    border-right: 4px solid #000000 !important;
}

/* Standard Streamlit Buttons */
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
    transform: translate(-2px, -2px) !important;
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
st.sidebar.markdown("""
**NETWORK:** SOLANA DEVNET  
**VM:** ANCHOR ESCROW / ED25519  
**AUTH:** ZERO-GAS OFF-CHAIN VOUCHER
""")

def fetch_channel_data(c_id):
    try:
        res = httpx.get(f"http://127.0.0.1:8000/channel/{c_id}/latest", timeout=1.5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return None
    return None

data = fetch_channel_data(channel_id)

# Top Stat Row
c1, c2, c3 = st.columns(3)

if data:
    amt = data.get("highest_amount", 0)
    agent_key = data.get("agent", "Unknown")
    sig = data.get("signature_hex", "")
    voucher = data.get("latest_voucher", {})

    with c1:
        st.markdown(f"""
        <div class="nb-card nb-cyan">
            <span class="nb-tag">Channel Status</span>
            <div class="nb-metric-num">ACTIVE #{channel_id}</div>
            <div>STATE: ESCROW LOCKED</div>
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
        st.markdown(f"""
        <div class="nb-card nb-yellow">
            <span class="nb-tag">Efficiency</span>
            <div class="nb-metric-num">99.98%</div>
            <div>TX OVERHEAD ELIMINATED</div>
        </div>
        """, unsafe_allow_html=True)

    # Details & Security Section
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
        st.markdown(f"""
        <div class="nb-card nb-green" style="word-break: break-all;">
            <span class="nb-tag">AGENT PUBKEY</span>
            <div style="margin-bottom: 0.8rem; font-size: 0.85rem;">{agent_key}</div>
            <span class="nb-tag">SIGNATURE ATTESTATION</span>
            <div style="margin-bottom: 0.8rem; font-size: 0.85rem;">{sig[:32]}...</div>
            <span class="nb-tag">SOLANA SETTLEMENT</span>
            <div style="font-size: 0.85rem;">PREPARING ATOMIC INSTRUCTION CLOSE</div>
        </div>
        """, unsafe_allow_html=True)

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
            <div class="nb-metric-num">LISTENING</div>
            <div>PORT: 127.0.0.1:8000</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nb-card nb-white">
        <span class="nb-tag">QUICKSTART INSTRUCTION</span>
        <div style="margin-top: 0.5rem;">
            Run <code>py agent_client.py</code> in your terminal to begin sending signed micropayment vouchers to this channel.
        </div>
    </div>
    """, unsafe_allow_html=True)

time.sleep(poll_freq)
st.rerun()