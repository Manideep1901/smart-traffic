"""
traffic_controller_demo.py

Streamlit app that simulates a 4-way intersection and runs a heuristic adaptive controller.
- Poisson arrivals per direction (configurable).
- Calls Flask API for phase & green time decision.
- Visualizes queues, current phase, average wait, and logs.

Run:
    streamlit run traffic_controller_demo.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import time
import math
import requests

# -----------------------------
# API-based Controller logic
# -----------------------------
def choose_phase_and_green(queues, last_served, params):
    """
    Call the Flask API to get phase & green time.
    Fallback to local heuristic if API fails.
    """
    url = "http://127.0.0.1:5000/decide"
    payload = {
        "counts": queues,
        "last_served": last_served
    }
    try:
        response = requests.post(url, json=payload, timeout=1.0)
        if response.status_code == 200:
            data = response.json()
            return data["phase"], data["green"]
        else:
            print("API call failed, using local heuristic. Status:", response.status_code)
            return local_heuristic(queues, last_served, params)
    except Exception as e:
        print("API exception:", e)
        return local_heuristic(queues, last_served, params)

# --- Local heuristic fallback ---
def local_heuristic(queues, last_served, params):
    S = params["S"]
    min_green = params["min_green"]
    max_green = params["max_green"]
    safety_buffer = params["safety_buffer"]
    cycle_target = params["cycle_target"]
    max_wait_threshold = params["max_wait_threshold"]
    alpha = params["alpha"]
    beta = params["beta"]

    # starvation check
    for d in ["N","E","S","W"]:
        if last_served.get(d, 0) >= max_wait_threshold and queues.get(d,0) > 0:
            chosen = d
            break
    else:
        scores = {d: alpha * queues.get(d,0) + beta * last_served.get(d,0) for d in ["N","E","S","W"]}
        chosen = max(scores, key=scores.get)

    q = queues.get(chosen,0)
    clear_t = q / S if S>0 else 0
    G = math.ceil(clear_t) + safety_buffer
    total_q = sum(queues.values())
    if total_q > 0 and q < 2:
        prop = q/max(1,total_q)
        G = max(1, int(round(prop * cycle_target)))
    G = max(min_green, min(max_green, G))
    return chosen, G

# -----------------------------
# Default parameters
# -----------------------------
DEFAULT_PARAMS = {
    "S": 1.8,                # saturation flow veh/s per lane
    "min_green": 8,
    "max_green": 45,
    "amber": 3,
    "all_red": 1,
    "safety_buffer": 3,
    "cycle_target": 60,
    "max_wait_threshold": 60,   # s before forced service
    "alpha": 1.0,
    "beta": 0.6,
    # arrivals (lambda veh/sec)
    "arrival_N": 0.2,
    "arrival_E": 0.15,
    "arrival_S": 0.4,
    "arrival_W": 0.1,
    "decision_interval": 1.0,   # run controller steps every 1 second (simulation tick)
}

# -----------------------------
# Streamlit UI + Session state init
# -----------------------------
st.set_page_config(page_title="Smart Traffic Controller Demo", layout="wide")
st.title("Smart Traffic Controller — 4-Way Intersection Prototype")

if "state_initialized" not in st.session_state:
    st.session_state.state_initialized = True
    st.session_state.params = DEFAULT_PARAMS.copy()
    st.session_state.queues = {"N": 0, "E": 0, "S": 0, "W": 0}
    st.session_state.last_served = {"N": 0, "E": 0, "S": 0, "W": 0}
    st.session_state.current_phase = None
    st.session_state.green_remaining = 0
    st.session_state.service_acc = 0.0
    st.session_state.running = False
    st.session_state.t = 0
    st.session_state.sum_wait = 0.0
    st.session_state.total_steps = 0
    st.session_state.logs = {"time": [], "N": [], "E": [], "S": [], "W": [], "phase": [], "avg_wait": [], "throughput": []}
    st.session_state.total_served = 0

# -----------------------------
# Sidebar controls (parameters)
# -----------------------------
st.sidebar.header("Simulation parameters")
p = st.sidebar
p_s = p.slider("Saturation flow (veh/s per lane)", 0.5, 3.5, value=float(st.session_state.params["S"]), step=0.1)
p_min_g = p.slider("Min green (s)", 4, 20, value=int(st.session_state.params["min_green"]))
p_max_g = p.slider("Max green (s)", 20, 120, value=int(st.session_state.params["max_green"]))
p_buffer = p.slider("Safety buffer (s)", 0, 6, value=int(st.session_state.params["safety_buffer"]))
p_max_wait = p.slider("Max wait before forced serve (s)", 30, 180, value=int(st.session_state.params["max_wait_threshold"]))
p_cycle = p.slider("Cycle target (s) for proportional allocation", 30, 120, value=int(st.session_state.params["cycle_target"]))
p_alpha = p.slider("Alpha (queue weight)", 0.0, 5.0, value=float(st.session_state.params["alpha"]), step=0.1)
p_beta = p.slider("Beta (wait weight)", 0.0, 5.0, value=float(st.session_state.params["beta"]), step=0.1)

st.sidebar.markdown("### Arrival rates (λ vehicles/sec)")
arrival_N = p.number_input("N (north) λ", min_value=0.0, max_value=10.0, value=float(st.session_state.params["arrival_N"]), step=0.05, format="%.3f")
arrival_E = p.number_input("E (east) λ", min_value=0.0, max_value=10.0, value=float(st.session_state.params["arrival_E"]), step=0.05, format="%.3f")
arrival_S = p.number_input("S (south) λ", min_value=0.0, max_value=10.0, value=float(st.session_state.params["arrival_S"]), step=0.05, format="%.3f")
arrival_W = p.number_input("W (west) λ", min_value=0.0, max_value=10.0, value=float(st.session_state.params["arrival_W"]), step=0.05, format="%.3f")

# update params
st.session_state.params.update({
    "S": p_s,
    "min_green": p_min_g,
    "max_green": p_max_g,
    "safety_buffer": p_buffer,
    "max_wait_threshold": p_max_wait,
    "cycle_target": p_cycle,
    "alpha": p_alpha,
    "beta": p_beta,
    "arrival_N": arrival_N,
    "arrival_E": arrival_E,
    "arrival_S": arrival_S,
    "arrival_W": arrival_W,
})

# -----------------------------
# Control buttons
# -----------------------------
colc1, colc2, colc3 = st.columns([1,1,2])
with colc1:
    if st.button("Start") or st.session_state.running:
        st.session_state.running = True
with colc2:
    if st.button("Stop"):
        st.session_state.running = False
with colc3:
    if st.button("Reset"):
        st.session_state.queues = {"N": 0, "E": 0, "S": 0, "W": 0}
        st.session_state.last_served = {"N": 0, "E": 0, "S": 0, "W": 0}
        st.session_state.current_phase = None
        st.session_state.green_remaining = 0
        st.session_state.service_acc = 0.0
        st.session_state.running = False
        st.session_state.t = 0
        st.session_state.sum_wait = 0.0
        st.session_state.total_steps = 0
        st.session_state.logs = {"time": [], "N": [], "E": [], "S": [], "W": [], "phase": [], "avg_wait": [], "throughput": []}
        st.session_state.total_served = 0

# -----------------------------
# Layout placeholders
# -----------------------------
left, right = st.columns([1,1])
with left:
    st.subheader("Intersection status")
    st.write("**Current phase**:", st.session_state.current_phase if st.session_state.current_phase else "—")
    st.write("**Green remaining (s):**", st.session_state.green_remaining)
    st.write("**Queues (vehicles)**")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("North (N)", st.session_state.queues["N"])
    q2.metric("East  (E)", st.session_state.queues["E"])
    q3.metric("South (S)", st.session_state.queues["S"])
    q4.metric("West  (W)", st.session_state.queues["W"])
    st.write("**Total served (vehicles)**", st.session_state.total_served)
    avg_wait_val = (st.session_state.sum_wait / st.session_state.total_steps) if st.session_state.total_steps>0 else 0.0
    st.write("**Avg queue length (over time)**: {:.2f}".format(avg_wait_val))

with right:
    st.subheader("Live charts")
    chart_placeholder = st.empty()
    phase_df_placeholder = st.empty()

# -----------------------------
# Simulation loop
# -----------------------------
if st.session_state.running:
    max_steps_per_run = 5000
    for _ in range(max_steps_per_run):
        st.session_state.t += 1
        st.session_state.total_steps += 1

        # arrivals (Poisson)
        st.session_state.queues["N"] += np.random.poisson(st.session_state.params["arrival_N"])
        st.session_state.queues["E"] += np.random.poisson(st.session_state.params["arrival_E"])
        st.session_state.queues["S"] += np.random.poisson(st.session_state.params["arrival_S"])
        st.session_state.queues["W"] += np.random.poisson(st.session_state.params["arrival_W"])

        st.session_state.sum_wait += sum(st.session_state.queues.values())

        # new phase if needed
        if st.session_state.green_remaining <= 0:
            chosen, G = choose_phase_and_green(st.session_state.queues, st.session_state.last_served, st.session_state.params)
            st.session_state.current_phase = chosen
            st.session_state.green_remaining = G
            st.session_state.service_acc = 0.0
            st.session_state.last_served[chosen] = 0

        # apply green
        if st.session_state.green_remaining > 0 and st.session_state.current_phase:
            st.session_state.service_acc += st.session_state.params["S"]
            to_remove = int(st.session_state.service_acc)
            if to_remove > 0:
                removed = min(st.session_state.queues[st.session_state.current_phase], to_remove)
                st.session_state.queues[st.session_state.current_phase] -= removed
                st.session_state.total_served += removed
                st.session_state.service_acc -= removed
            st.session_state.green_remaining -= 1

        # increment last_served timers
        for d in ["N","E","S","W"]:
            if d != st.session_state.current_phase:
                st.session_state.last_served[d] += 1

        # log for charts
        st.session_state.logs["time"].append(st.session_state.t)
        st.session_state.logs["N"].append(st.session_state.queues["N"])
        st.session_state.logs["E"].append(st.session_state.queues["E"])
        st.session_state.logs["S"].append(st.session_state.queues["S"])
        st.session_state.logs["W"].append(st.session_state.queues["W"])
        st.session_state.logs["phase"].append(st.session_state.current_phase)
        st.session_state.logs["avg_wait"].append(st.session_state.sum_wait / max(1, st.session_state.total_steps))
        st.session_state.logs["throughput"].append(st.session_state.total_served)

        # update charts
        df = pd.DataFrame({
            "N": st.session_state.logs["N"][-200:],
            "E": st.session_state.logs["E"][-200:],
            "S": st.session_state.logs["S"][-200:],
            "W": st.session_state.logs["W"][-200:],
        }, index=st.session_state.logs["time"][-200:])
        with chart_placeholder.container():
            st.line_chart(df)
        with phase_df_placeholder.container():
            st.write("Last chosen phase:", st.session_state.current_phase, " | green remaining:", st.session_state.green_remaining)
            st.write("Avg queue length (historical): {:.2f}".format(st.session_state.logs["avg_wait"][-1]))
            st.write("Total vehicles served:", st.session_state.total_served)

        time.sleep(st.session_state.params["decision_interval"])
        if not st.session_state.running:
            break

    st.experimental_rerun()
else:
    st.info("Press **Start** to run the simulation. Make sure controller_api.py is running on port 5000.")
