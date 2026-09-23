# sumo_bridge.py
import traci
import time
import requests
import argparse
import sys
import os

# -------------------------
# Configuration & Topology
# -------------------------
JUNCTION_LANE_MAP = {
    # Single 4-way junction
    "C": {
        "N": ["NtoC_0", "NtoC_1"],
        "E": ["EtoC_0", "EtoC_1"],
        "S": ["StoC_0", "StoC_1"],
        "W": ["WtoC_0", "WtoC_1"],
    },
    # Multi-junction 2x3 network
    "J1": {
        "N": ["N1toJ1_0", "N1toJ1_1"],
        "E": ["J2toJ1_0", "J2toJ1_1"],
        "S": ["J4toJ1_0", "J4toJ1_1"],
        "W": ["W1toJ1_0", "W1toJ1_1"],
    },
    "J2": {
        "N": ["N2toJ2_0", "N2toJ2_1"],
        "E": ["J3toJ2_0", "J3toJ2_1"],
        "S": ["J5toJ2_0", "J5toJ2_1"],
        "W": ["J1toJ2_0", "J1toJ2_1"],
    },
    "J3": {
        "N": ["N3toJ3_0", "N3toJ3_1"],
        "E": ["E1toJ3_0", "E1toJ3_1"],
        "S": ["J6toJ3_0", "J6toJ3_1"],
        "W": ["J2toJ3_0", "J2toJ3_1"],
    },
    "J4": {
        "N": ["J1toJ4_0", "J1toJ4_1"],
        "E": ["J5toJ4_0", "J5toJ4_1"],
        "S": ["S1toJ4_0", "S1toJ4_1"],
        "W": ["W2toJ4_0", "W2toJ4_1"],
    },
    "J5": {
        "N": ["J2toJ5_0", "J2toJ5_1"],
        "E": ["J6toJ5_0", "J6toJ5_1"],
        "S": ["S2toJ5_0", "S2toJ5_1"],
        "W": ["J4toJ5_0", "J4toJ5_1"],
    },
    "J6": {
        "N": ["J3toJ6_0", "J3toJ6_1"],
        "E": ["E2toJ6_0", "E2toJ6_1"],
        "S": ["S3toJ6_0", "S3toJ6_1"],
        "W": ["J5toJ6_0", "J5toJ6_1"],
    }
}

class JunctionControllerState:
    def __init__(self, j_id):
        self.j_id = j_id
        self.green_active = False
        self.green_end_time = -1.0
        self.all_red_duration = 1.0
        self.all_red_active = False
        self.all_red_end = -1.0
        self.current_phase_idx = None
        self.chosen = None

def resolve_tls_phase_maps():
    phase_maps = {}
    active_tls = traci.trafficlight.getIDList()
    for j_id in active_tls:
        lanes = traci.trafficlight.getControlledLanes(j_id)
        logics = traci.trafficlight.getAllProgramLogics(j_id)
        if not logics:
            phase_maps[j_id] = {"total": 4, "NS_GREEN": 0, "NS_YELLOW": 1, "EW_GREEN": 2, "EW_YELLOW": 3}
            continue
        phases = logics[0].phases
        ns_lanes = set(JUNCTION_LANE_MAP.get(j_id, {}).get("N", []) + JUNCTION_LANE_MAP.get(j_id, {}).get("S", []))
        ew_lanes = set(JUNCTION_LANE_MAP.get(j_id, {}).get("E", []) + JUNCTION_LANE_MAP.get(j_id, {}).get("W", []))
        
        mapping = {"total": len(phases)}
        for idx, p in enumerate(phases):
            state = p.state
            ns_green = any(ln in ns_lanes and state[i] in "Gg" for i, ln in enumerate(lanes))
            ew_green = any(ln in ew_lanes and state[i] in "Gg" for i, ln in enumerate(lanes))
            ns_yellow = any(ln in ns_lanes and state[i] in "yY" for i, ln in enumerate(lanes))
            ew_yellow = any(ln in ew_lanes and state[i] in "yY" for i, ln in enumerate(lanes))
            
            if ns_green and not ew_green and "NS_GREEN" not in mapping:
                mapping["NS_GREEN"] = idx
            elif ew_green and not ns_green and "EW_GREEN" not in mapping:
                mapping["EW_GREEN"] = idx
            elif ns_yellow and not ew_yellow and "NS_YELLOW" not in mapping:
                mapping["NS_YELLOW"] = idx
            elif ew_yellow and not ns_yellow and "EW_YELLOW" not in mapping:
                mapping["EW_YELLOW"] = idx
        
        if "NS_GREEN" not in mapping:
            mapping["NS_GREEN"] = 0
        if "NS_YELLOW" not in mapping:
            mapping["NS_YELLOW"] = (mapping["NS_GREEN"] + 1) % mapping["total"]
        if "EW_GREEN" not in mapping:
            mapping["EW_GREEN"] = (mapping["NS_YELLOW"] + 1) % mapping["total"]
        if "EW_YELLOW" not in mapping:
            mapping["EW_YELLOW"] = (mapping["EW_GREEN"] + 1) % mapping["total"]
            
        phase_maps[j_id] = mapping
    return phase_maps

def dir_to_phase(j_id, chosen, phase_maps):
    m = phase_maps.get(j_id, {})
    if chosen in ("N", "S"):
        return m.get("NS_GREEN", 0)
    else:
        return m.get("EW_GREEN", 2)

def get_yellow_phase(j_id, current_phase_idx, phase_maps):
    m = phase_maps.get(j_id, {})
    if current_phase_idx == m.get("NS_GREEN"):
        return m.get("NS_YELLOW", (current_phase_idx + 1) % m.get("total", 4))
    elif current_phase_idx == m.get("EW_GREEN"):
        return m.get("EW_YELLOW", (current_phase_idx + 1) % m.get("total", 4))
    else:
        return (current_phase_idx + 1) % m.get("total", 4)

def set_safe_phase(tls_id, phase_idx, duration=None, phase_maps=None):
    total = phase_maps.get(tls_id, {}).get("total", 4) if phase_maps else 4
    if not (0 <= phase_idx < total):
        print(f"[ERROR] TLS {tls_id}: Requested phase {phase_idx} outside range [0, {total - 1}]")
        phase_idx = max(0, min(total - 1, phase_idx))
    traci.trafficlight.setPhase(tls_id, phase_idx)
    if duration is not None:
        traci.trafficlight.setPhaseDuration(tls_id, float(duration))

def get_lane_counts(j_id):
    lanes = JUNCTION_LANE_MAP.get(j_id, {})
    counts = {}
    for d, lane_list in lanes.items():
        total = 0
        for l in lane_list:
            try:
                total += traci.lane.getLastStepVehicleNumber(l)
            except Exception:
                pass
        counts[d] = total
    return counts

def request_decision(j_id, counts):
    url = "http://127.0.0.1:5000/decide"
    try:
        r = requests.post(url, json={"junction": j_id, "counts": counts}, timeout=1.0)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"[{j_id}] Controller API status: {r.status_code}")
    except Exception as e:
        pass
    # Fallback heuristic: serve direction with highest queue
    maxd = max(counts, key=counts.get) if counts else "N"
    return {"phase": maxd, "green": 10, "junction": j_id}

# -------------------------
# Main Simulation Loop
# -------------------------
def run_simulation(sumo_cfg="multi_junction.sumocfg", gui=False, max_steps=200000):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(sumo_cfg):
        if not os.path.exists(sumo_cfg) and os.path.exists(os.path.join(script_dir, sumo_cfg)):
            sumo_cfg = os.path.join(script_dir, sumo_cfg)

    cmd_name = "sumo-gui" if gui else "sumo"
    sumo_cmd = [cmd_name, "-c", sumo_cfg]

    print(f"Starting SUMO TraCI with command: {' '.join(sumo_cmd)}")
    traci.start(sumo_cmd)
    print("SUMO started via TraCI successfully.")

    # Discover active traffic lights and resolve phase maps
    active_tls = traci.trafficlight.getIDList()
    phase_maps = resolve_tls_phase_maps()
    print(f"Discovered Traffic Lights in simulation: {active_tls}")
    print(f"Resolved TLS Phase Maps: {phase_maps}")

    states = {tls: JunctionControllerState(tls) for tls in active_tls if tls in JUNCTION_LANE_MAP}
    if not states:
        # Fallback if unknown IDs
        states = {tls: JunctionControllerState(tls) for tls in active_tls}

    step = 0
    while step < max_steps:
        traci.simulationStep()
        sim_time = traci.simulation.getTime()

        # Step each traffic light junction controller
        for j_id, state in states.items():
            counts = get_lane_counts(j_id)

            # Check if yellow/clearance gap active
            if state.all_red_active:
                if sim_time >= state.all_red_end:
                    state.all_red_active = False
                else:
                    continue

            # Check if green expired -> trigger transition to yellow
            if state.green_active and sim_time >= state.green_end_time:
                yellow_phase = get_yellow_phase(j_id, state.current_phase_idx, phase_maps)
                set_safe_phase(j_id, yellow_phase, state.all_red_duration, phase_maps)
                state.all_red_active = True
                state.all_red_end = sim_time + state.all_red_duration
                state.green_active = False
                continue

            # If no green active, request new decision
            if not state.green_active:
                decision = request_decision(j_id, counts)
                chosen = decision.get("phase", "N")
                green = int(decision.get("green", 10))
                phase_idx = dir_to_phase(j_id, chosen, phase_maps)

                set_safe_phase(j_id, phase_idx, green, phase_maps)

                state.green_active = True
                state.green_end_time = sim_time + green
                state.current_phase_idx = phase_idx
                state.chosen = chosen

                if step % 20 == 0:
                    print(f"[t={sim_time:5.1f}] [{j_id}] START: serve {chosen} for {green}s (phase {phase_idx}) | counts={counts}")

        # Summary print every 50 steps
        if step % 50 == 0 and step > 0:
            veh_count = traci.vehicle.getIDCount()
            print(f"[t={sim_time:5.1f}] Running simulation: Active vehicles in network = {veh_count}")

        step += 1
        if gui:
            time.sleep(0.01)

    traci.close()
    print("Simulation completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SUMO Multi-Junction TraCI Bridge")
    parser.add_argument("--cfg", type=str, default="multi_junction.sumocfg", help="SUMO config file (multi_junction.sumocfg or 4way.sumocfg)")
    parser.add_argument("--gui", action="store_true", help="Launch sumo-gui instead of headless sumo")
    parser.add_argument("--steps", type=int, default=200000, help="Number of simulation steps")
    args = parser.parse_args()

    run_simulation(sumo_cfg=args.cfg, gui=args.gui, max_steps=args.steps)
