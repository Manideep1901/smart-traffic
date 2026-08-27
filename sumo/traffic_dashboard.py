# traffic_dashboard.py
import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

API_BASE = "http://127.0.0.1:5000"

st.set_page_config(layout="wide", page_title="Multi-Junction Smart Traffic Dashboard")

st.title("🚦 Smart Traffic Multi-Junction Control — Live Dashboard")

# Top controls
col_ctrl1, col_ctrl2 = st.columns([2, 1])
with col_ctrl1:
    junction_option = st.selectbox(
        "Select Junction / View",
        ["Network Overview (All)", "J1", "J2", "J3", "J4", "J5", "J6", "C"]
    )

with col_ctrl2:
    history_len = st.slider("History points", min_value=20, max_value=500, value=100, step=20)

# Layout placeholders
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Signal & Queue Status")
    phase_box = st.empty()
    countdown_box = st.empty()
    metrics_box = st.empty()
    serve_table = st.empty()

with col2:
    st.subheader("Lane Densities & Historical Trends")
    counts_cols = st.columns(4)
    pN = counts_cols[0].empty()
    pE = counts_cols[1].empty()
    pS = counts_cols[2].empty()
    pW = counts_cols[3].empty()

    chart_placeholder = st.empty()

# Log Area
st.subheader("Recent Controller Decisions")
log_placeholder = st.empty()

# Session State for History
if "history" not in st.session_state:
    st.session_state.history = []

REFRESH_SEC = 1.0

def get_status():
    try:
        r = requests.get(API_BASE + "/get_status", timeout=1.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None

# Main dashboard refresh loop
while True:
    status = get_status()
    if status is None:
        st.warning("Connecting to Controller API (http://127.0.0.1:5000)... Make sure controller_api.py is running.")
        time.sleep(1.5)
        continue

    junctions_data = status.get("junctions", {})
    ts = datetime.fromtimestamp(status.get("timestamp", time.time())).strftime("%H:%M:%S")

    # Determine counts and decision based on selected junction
    if junction_option == "Network Overview (All)" or not junctions_data:
        counts = status.get("counts", {"N": 0, "E": 0, "S": 0, "W": 0})
        last_decision = status.get("last_decision", {})
        view_title = "Network Totals"
    else:
        j_info = junctions_data.get(junction_option, {})
        counts = j_info.get("counts", {"N": 0, "E": 0, "S": 0, "W": 0})
        last_decision = j_info.get("last_decision", {})
        view_title = f"Junction {junction_option}"

    # Update metric counters
    pN.metric("North (N)", counts.get("N", 0))
    pE.metric("East  (E)", counts.get("E", 0))
    pS.metric("South (S)", counts.get("S", 0))
    pW.metric("West  (W)", counts.get("W", 0))

    # Show active phase and countdown
    phase = last_decision.get("phase", "—")
    green = last_decision.get("green", 0) or 0
    end_time = last_decision.get("end_time")
    now_ts = time.time()
    remaining = max(0, int(end_time - now_ts)) if end_time else 0

    phase_box.markdown(f"**{view_title} Serving:**  `Phase {phase}`")
    countdown_box.markdown(f"**Green Duration Remaining:**  `{remaining} s` (Allocated: `{green} s`)")

    # Summary metrics
    avg_queue = (counts.get("N", 0) + counts.get("E", 0) + counts.get("S", 0) + counts.get("W", 0)) / 4.0
    active_j_count = len(junctions_data) if junctions_data else 1
    metrics_box.markdown(f"- **Avg Queue**: `{avg_queue:.1f}`\n- **Active Controlled Junctions**: `{active_j_count}`\n- **Last Sync**: `{ts}`")

    # Record history
    rec = {
        "time": ts,
        "view": junction_option,
        "N": counts.get("N", 0),
        "E": counts.get("E", 0),
        "S": counts.get("S", 0),
        "W": counts.get("W", 0),
        "phase": phase,
        "green": green
    }
    st.session_state.history.append(rec)
    if len(st.session_state.history) > 2000:
        st.session_state.history = st.session_state.history[-2000:]

    # Build DataFrame for charts
    df = pd.DataFrame(st.session_state.history[-history_len:])
    if not df.empty and "N" in df.columns:
        chart_df = df[["N", "E", "S", "W"]].rename(columns={"N": "North", "E": "East", "S": "South", "W": "West"})
        chart_placeholder.line_chart(chart_df)

    # Show recent decisions table
    if not df.empty:
        recent = df[["time", "view", "phase", "green", "N", "E", "S", "W"]].tail(8).iloc[::-1]
        serve_table.table(recent)

    # Log text
    latest = st.session_state.history[-5:]
    log_lines = [f"{r['time']} | [{r['view']}] phase={r['phase']} ({r['green']}s) | Queues: N={r['N']} E={r['E']} S={r['S']} W={r['W']}" for r in latest[::-1]]
    log_placeholder.markdown("\n".join(log_lines))

    time.sleep(REFRESH_SEC)
