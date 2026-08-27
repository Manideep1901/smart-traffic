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

def dir_to_phase(chosen, total_phases=6):
    """
    Map direction N/S to NS Green, E/W to EW Green.
    In 6-phase add.xml: 0=NS Green, 1=NS Yellow, 2=AllRed, 3=EW Green, 4=EW Yellow, 5=AllRed.
    In 4-phase add.xml: 0=NS Green, 1=AllRed, 2=EW Green, 3=AllRed.
    """
    if total_phases == 6:
        return 0 if chosen in ("N", "S") else 3
    else:
        return 0 if chosen in ("N", "S") else 2

def get_all_red_phase(current_phase_idx, total_phases=6):
    if total_phases == 6:
        return 2 if current_phase_idx in (0, 1) else 5
    else:
        return 1 if current_phase_idx == 0 else 3

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
    cmd_name = "sumo-gui" if gui else "sumo"
    sumo_cmd = [cmd_name, "-c", sumo_cfg]

    print(f"Starting SUMO TraCI with command: {' '.join(sumo_cmd)}")
    traci.start(sumo_cmd)
    print("SUMO started via TraCI successfully.")

    # Discover active traffic lights
    active_tls = traci.trafficlight.getIDList()
    print(f"Discovered Traffic Lights in simulation: {active_tls}")

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
            num_phases = len(traci.trafficlight.getAllProgramLogics(j_id)[0].phases) if traci.trafficlight.getAllProgramLogics(j_id) else 6

            # Check if all-red gap active
            if state.all_red_active:
                if sim_time >= state.all_red_end:
                    state.all_red_active = False
                else:
                    continue

            # Check if green expired -> trigger transition to all-red
            if state.green_active and sim_time >= state.green_end_time:
                all_red_phase = get_all_red_phase(state.current_phase_idx, num_phases)
                try:
                    traci.trafficlight.setPhase(j_id, all_red_phase)
                    traci.trafficlight.setPhaseDuration(j_id, state.all_red_duration)
                except Exception:
                    pass
                state.all_red_active = True
                state.all_red_end = sim_time + state.all_red_duration
                state.green_active = False
                continue

            # If no green active, request new decision
            if not state.green_active:
                decision = request_decision(j_id, counts)
                chosen = decision.get("phase", "N")
                green = int(decision.get("green", 10))
                phase_idx = dir_to_phase(chosen, num_phases)

                try:
                    traci.trafficlight.setPhase(j_id, phase_idx)
                    traci.trafficlight.setPhaseDuration(j_id, green)
                except Exception as ex:
                    print(f"Error setting phase for {j_id}: {ex}")

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
    parser.add_argument("--steps", type=int, default=2000, help="Number of simulation steps")
    args = parser.parse_args()

    run_simulation(sumo_cfg=args.cfg, gui=args.gui, max_steps=args.steps)
