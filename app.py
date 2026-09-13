import streamlit as st
import httpx
import json
import time
import html
from embedded_agent import EmbeddedAgent

st.set_page_config(
    page_title="SYNAPSEPAY // AGENT PROTOCOL",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROXY_URL = "https://synapsepay-proxy.onrender.com"

# ---------------------------------------------------------
# 00 // THEME CONFIGURATION & PALETTE MAPPING
# ---------------------------------------------------------
st.sidebar.markdown("### 00 // THEME CONFIG")
dark_mode = st.sidebar.toggle("🌙 DARK MODE", value=True)

if dark_mode:
    bg_app = "#0A0A0C"
    bg_sidebar = "#121316"
    border_color = "#2A2D35"
    text_color = "#F0F0F0"
    btn_bg = "#00FFA3"
    btn_border = "#00FF66"
    btn_shadow = "#003B22"
    btn_hover_bg = "#FF0055"
    input_bg = "#16181D"
    card_json_bg = "#0E1015"
    card_json_color = "#00FFA3"
    c1_bg = "#0B1E28"; c1_border = "#00E5FF"; c1_shadow = "#004D5A"; c1_num = "#00E5FF"; c1_sub = "#A5F3FC"
    c2_bg = "#260D1A"; c2_border = "#FF007F"; c2_shadow = "#5E002E"; c2_num = "#FF007F"; c2_sub = "#FBCFE8"
    c3_bg = "#242008"; c3_border = "#FFE600"; c3_shadow = "#544C00"; c3_num = "#FFE600"; c3_sub = "#FEF08A"
    green_bg = "#0B2416"; green_border = "#00FF85"; green_sub = "#A7F3D0"
    link_color = "#00FFA3"
    tag_bg = "#000000"
    tag_color = "#00FFA3"
else:
    bg_app = "#FFFDF0"
    bg_sidebar = "#FFFDF0"
    border_color = "#000000"
    text_color = "#000000"
    btn_bg = "#FFE600"
    btn_border = "#000000"
    btn_shadow = "#000000"
    btn_hover_bg = "#FF5252"
    input_bg = "#FFFFFF"
    card_json_bg = "#FFFFFF"
    card_json_color = "#000000"
    c1_bg = "#70D6FF"; c1_border = "#000000"; c1_shadow = "#000000"; c1_num = "#000000"; c1_sub = "#000000"
    c2_bg = "#FF70A6"; c2_border = "#000000"; c2_shadow = "#000000"; c2_num = "#000000"; c2_sub = "#000000"
    c3_bg = "#FFD670"; c3_border = "#000000"; c3_shadow = "#000000"; c3_num = "#000000"; c3_sub = "#000000"
    green_bg = "#79FF85"; green_border = "#000000"; green_sub = "#000000"
    link_color = "#000000"
    tag_bg = "#000000"
    tag_color = "#FFFFFF"

# Dynamic CSS Injection
st.markdown(f"""
<style>
.stApp {{
    background-color: {bg_app} !important;
    font-family: 'Courier New', Courier, monospace, sans-serif !important;
    color: {text_color} !important;
}}
[data-testid="stSidebar"] {{
    background-color: {bg_sidebar} !important;
    border-right: 3px solid {border_color} !important;
}}
[data-testid="stSidebar"] * {{
    color: {text_color} !important;
}}
h1, h2, h3, h4, p, span, label {{
    color: {text_color} !important;
    font-family: 'Courier New', Courier, monospace, sans-serif !important;
}}
.stButton > button {{
    background-color: {btn_bg} !important;
    color: #000000 !important;
    border: 3px solid {btn_border} !important;
    border-radius: 0px !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    padding: 0.5rem 1.2rem !important;
    box-shadow: 4px 4px 0px {btn_shadow} !important;
    transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}}
.stButton > button:hover {{
    transform: translate(-2px, -2px) !important;
    box-shadow: 6px 6px 0px {btn_border} !important;
    background-color: {btn_hover_bg} !important;
    color: #FFFFFF !important;
}}
.stButton > button:active {{
    transform: translate(2px, 2px) !important;
    box-shadow: 1px 1px 0px #000000 !important;
}}
.stTextInput input, .stNumberInput input {{
    background-color: {input_bg} !important;
    border: 2px solid {border_color} !important;
    border-radius: 0px !important;
    color: {text_color} !important;
    font-weight: 700 !important;
    box-shadow: 3px 3px 0px #000000 !important;
}}
.nb-card {{
    border: 3px solid {border_color};
    box-shadow: 5px 5px 0px {btn_shadow};
    padding: 1.2rem;
    margin-bottom: 1.5rem;
    font-weight: bold;
}}
.nb-tag {{
    display: inline-block;
    background: {tag_bg};
    color: {tag_color};
    font-size: 0.72rem;
    font-weight: 900;
    padding: 2px 8px;
    margin-bottom: 8px;
    text-transform: uppercase;
    border: 1px solid {border_color};
}}
.nb-metric-num {{
    font-size: 2.2rem;
    font-weight: 900;
    line-height: 1.1;
    margin: 0.3rem 0;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown(f"""
<div style="border-bottom: 3px solid {border_color}; padding-bottom: 0.8rem; margin-bottom: 1.5rem;">
    <h1 style="font-size: 2.3rem; font-weight: 900; text-transform: uppercase; margin: 0; color: {btn_bg};">
        ⚡ SYNAPSEPAY // AGENT SETTLEMENT GATEWAY
    </h1>
    <p style="font-weight: 700; margin: 0.3rem 0 0 0; opacity: 0.85;">
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


# ---------------------------------------------------------
# 01 // SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.markdown("### 01 // CONTROL PANEL")

# Hardcoded initial default 101; accepts any positive integer ID
channel_id = st.sidebar.number_input("TARGET CHANNEL ID", min_value=1, value=101, step=1)

# Dynamically bind agent simulator to channel_id upon selection
if "active_channel_id" not in st.session_state or st.session_state.active_channel_id != channel_id:
    st.session_state.active_channel_id = channel_id
    st.session_state.agent_sim = EmbeddedAgent(PROXY_URL, channel_id)
    st.session_state.last_tx = None

st.sidebar.markdown("---")
st.sidebar.markdown("### 02 // STREAM CONFIG")
auto_stream = st.sidebar.toggle("ENABLE CONTINUOUS STREAM", value=True)
stream_step = st.sidebar.select_slider("STEP SIZE (μ-UNITS)", options=[10, 20, 50, 100, 250, 500], value=20)
poll_freq = st.sidebar.slider("STREAM INTERVAL (SEC)", min_value=1, max_value=5, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**CLUSTER:** SOLANA DEVNET  
**CRYPTO:** ED25519 NATIVE  
**ROUTING:** MONOTONIC STATE CHANNEL  
""")

# Safe backend state lookup with defensive fallbacks
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

# ---------------------------------------------------------
# METRICS ROW
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)

if isinstance(data, dict) and data.get("highest_amount", 0) > 0:
    amt = data.get("highest_amount", 0)
    agent_key = data.get("agent", "Unknown")
    sig = data.get("signature_hex", "")
    voucher = data.get("latest_voucher", {})
    status_label = "STATE: SETTLED ON-CHAIN" if is_settled else "STATE: ESCROW LOCKED"

    with c1:
        st.markdown(f"""
        <div class="nb-card" style="background-color: {c1_bg}; border-color: {c1_border}; box-shadow: 5px 5px 0px {c1_shadow};">
            <span class="nb-tag">Channel Status</span>
            <div class="nb-metric-num" style="color: {c1_num} !important;">ACTIVE #{channel_id}</div>
            <div style="color: {c1_sub};">{html.escape(status_label)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="nb-card" style="background-color: {c2_bg}; border-color: {c2_border}; box-shadow: 5px 5px 0px {c2_shadow};">
            <span class="nb-tag">Cumulative Balance</span>
            <div class="nb-metric-num" style="color: {c2_num} !important;">{amt:,} μ-UNITS</div>
            <div style="color: {c2_sub};">VALIDATED MONOTONIC STREAM</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="nb-card" style="background-color: {c3_bg}; border-color: {c3_border}; box-shadow: 5px 5px 0px {c3_shadow};">
            <span class="nb-tag">Network Efficiency</span>
            <div class="nb-metric-num" style="color: {c3_num} !important;">99.98%</div>
            <div style="color: {c3_sub};">TX OVERHEAD ELIMINATED</div>
        </div>
        """, unsafe_allow_html=True)

    # Manual Control Bar
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

    # Split Detail Workspace
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### 03 // OFF-CHAIN ED25519 VOUCHER")
        pretty_json = html.escape(json.dumps(voucher, indent=2))
        st.markdown(f"""
        <div class="nb-card" style="background-color: {card_json_bg}; border-color: {border_color};">
            <pre style="margin:0; font-weight:700; color: {card_json_color}; font-size: 0.88rem;">{pretty_json}</pre>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 04 // ON-CHAIN SETTLEMENT PDA")

        # Devnet Settlement Trigger
        if not is_settled:
            if st.button("⚡ EXECUTE DEVNET SETTLEMENT NOW"):
                with st.spinner("Broadcasting atomic close instruction to Solana Devnet..."):
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
                f'target="_blank" style="color:{link_color}; text-decoration: underline; font-weight: 900;">'
                f'VIEW CONFIRMED TX ON EXPLORER ↗</a>'
            )
        else:
            settle_status_html = '<span style="opacity: 0.8;">ESCROW ACTIVE // AWAITING CLOSE INSTRUCTION</span>'

        safe_agent = html.escape(str(agent_key))
        safe_sig = html.escape(str(sig[:32])) + "..."

        pda_card_html = f"""
        <div class="nb-card" style="background-color: {green_bg}; border-color: {green_border}; word-break: break-all;">
            <span class="nb-tag">AGENT PUBKEY</span>
            <div style="margin-bottom: 0.8rem; font-size: 0.85rem; color: {green_sub};">{safe_agent}</div>
            <span class="nb-tag">SIGNATURE ATTESTATION</span>
            <div style="margin-bottom: 0.8rem; font-size: 0.85rem; color: {green_sub};">{safe_sig}</div>
            <span class="nb-tag">SOLANA SETTLEMENT</span>
            <div style="font-size: 0.85rem; font-weight: 900; margin-top: 4px;">{settle_status_html}</div>
        </div>
        """
        st.markdown(pda_card_html, unsafe_allow_html=True)

else:
    # Cold-Start / Backend Sleeping State
    with c1:
        st.markdown(f"""
        <div class="nb-card" style="background-color: {c2_bg}; border-color: {c2_border}; box-shadow: 5px 5px 0px {c2_shadow};">
            <span class="nb-tag">Channel Status</span>
            <div class="nb-metric-num" style="color: {c2_num} !important;">IDLE #{channel_id}</div>
            <div style="color: {c2_sub};">WAITING FOR AGENT CALLS</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="nb-card" style="background-color: {c3_bg}; border-color: {c3_border}; box-shadow: 5px 5px 0px {c3_shadow};">
            <span class="nb-tag">Cumulative Balance</span>
            <div class="nb-metric-num" style="color: {c3_num} !important;">0 μ-UNITS</div>
            <div style="color: {c3_sub};">NO RECENT INVOCATIONS</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="nb-card" style="background-color: {c1_bg}; border-color: {c1_border}; box-shadow: 5px 5px 0px {c1_shadow};">
            <span class="nb-tag">Proxy Health</span>
            <div class="nb-metric-num" style="color: {c1_num} !important;">ONLINE</div>
            <div style="color: {c1_sub};">READY FOR INGESTION</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="nb-card" style="background-color: {card_json_bg}; border-color: {border_color};">
        <span class="nb-tag">SYSTEM STATUS</span>
        <div style="margin-top: 0.5rem; font-weight: 700;">
            Channel #{channel_id} is ready. Keep <b>ENABLE CONTINUOUS STREAM</b> active or dispatch initial micro-payments below to start streaming signed vouchers.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ DISPATCH INITIAL VOUCHER (+20)"):
        st.session_state.agent_sim.trigger_micro_payment(current_total=0, step=20)
        st.rerun()

# Rerun cycle for continuous auto-streaming
if auto_stream and not is_settled:
    time.sleep(poll_freq)
    st.rerun()