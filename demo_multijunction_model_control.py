"""
demo_multijunction_model_control.py

Adaptive SUMO Traffic Control System for Multi-Junction Network (2x3 Grid: J1 to J6):
1. Displays real-time vehicle counts per approach (N, E, S, W) for ALL 6 junctions.
2. Decentralized AI Model calculates priority scores (Queue + 0.6 * Wait) for each junction.
3. Computes exact required green duration per junction.
4. Executes traffic light phase changes with yellow/all-red transitions.
5. Displays step-by-step green signal execution and network-wide vehicle metrics.
"""

import os
import sys
import time
import argparse
import numpy as np
import traci

# Topology map for 2x3 Multi-Junction Grid
JUNCTION_LANE_MAP = {
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


class SmartTrafficModel:
    """
    Decentralized AI Traffic Control Model for an individual junction:
    Priority Score = Queue_Length + 0.6 * Wait_Time
    Calculates required green duration (8s to 25s).
    """
    def __init__(self, junction_id):
        self.junction_id = junction_id
        self.directions = ["N", "E", "S", "W"]
        self.last_served = {"N": 0, "E": 0, "S": 0, "W": 0}
        self.alpha = 1.0  # Weight for queue count
        self.beta = 0.6   # Weight for wait time

    def calculate_decision(self, counts):
        scores = {}
        for d in self.directions:
            q = counts.get(d, 0)
            w = self.last_served.get(d, 0)
            scores[d] = round(self.alpha * q + self.beta * w, 1)

        chosen_dir = max(scores, key=scores.get)
        target_queue = counts.get(chosen_dir, 0)

        if target_queue == 0:
            green_duration = 8
        else:
            clear_time = int(np.ceil(target_queue / 1.8)) + 3
            green_duration = max(8, min(25, clear_time))

        # Update wait timers
        for d in self.directions:
            if d == chosen_dir:
                self.last_served[d] = 0
            else:
                self.last_served[d] += green_duration + 2

        return chosen_dir, green_duration, scores


def get_junction_counts(j_id):
    """Fetches vehicle counts per approach for a specific junction."""
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


def get_target_phase(chosen_dir):
    """
    In 6-phase add.xml:
      Phase 0: NS Green
      Phase 1: NS Yellow
      Phase 2: All-Red
      Phase 3: EW Green
      Phase 4: EW Yellow
      Phase 5: All-Red
    """
    return 0 if chosen_dir in ["N", "S"] else 3


def run_multijunction_demo(gui=False, cycles=10, cfg_path="sumo/multi_junction.sumocfg"):
    if not os.path.exists(cfg_path):
        if os.path.exists("multi_junction.sumocfg"):
            cfg_path = "multi_junction.sumocfg"
        else:
            print(f"Error: SUMO config file '{cfg_path}' not found.")
            return

    cmd = "sumo-gui" if gui else "sumo"
    print("=" * 85)
    print("      [SMART TRAFFIC MANAGEMENT SYSTEM] -- MULTI-JUNCTION AI SIGNAL CONTROL DEMO")
    print("=" * 85)
    print(f" Executing via: {'SUMO GUI Visual Window' if gui else 'Headless Console'}")
    print(f" Configuration: {cfg_path}")
    print(f" Network Grid : 6 Interconnected Junctions (J1, J2, J3, J4, J5, J6)")
    print("=" * 85)

    traci.start([cmd, "-c", cfg_path, "--start", "--quit-on-end"])
    print("\n[OK] SUMO TraCI initialized successfully.")

    junction_ids = ["J1", "J2", "J3", "J4", "J5", "J6"]
    models = {j_id: SmartTrafficModel(j_id) for j_id in junction_ids}

    # Warm-up simulation for 5 seconds so traffic enters the grid
    print("[INIT] Spawning traffic flow across all 6 junctions in the 2x3 network...")
    for _ in range(50):
        traci.simulationStep()

    dir_names = {"N": "NORTH", "E": "EAST", "S": "SOUTH", "W": "WEST"}

    try:
        for cycle in range(1, cycles + 1):
            sim_time = traci.simulation.getTime()
            active_vehs = traci.vehicle.getIDCount()

            print("\n" + "=" * 85)
            print(f"  MULTI-JUNCTION DECISION CYCLE {cycle} OF {cycles}  |  SUMO Sim Time: {sim_time:.1f}s")
            print("=" * 85)

            # Step 1: Read vehicle counts for all 6 junctions
            all_counts = {}
            print("\n1. REAL-TIME VEHICLE COUNTS PER JUNCTION APPROACH:")
            print("   " + "-" * 75)
            print("   Junction | North (N) | East (E)  | South (S) | West (W)  | Total Queue")
            print("   " + "-" * 75)
            for j_id in junction_ids:
                counts = get_junction_counts(j_id)
                all_counts[j_id] = counts
                tot_q = sum(counts.values())
                print(f"     {j_id:5s}  |  {counts['N']:2d} vehs   |  {counts['E']:2d} vehs   |  {counts['S']:2d} vehs   |  {counts['W']:2d} vehs   |   {tot_q:2d} vehs")
            print("   " + "-" * 75)
            print(f"   Total Active Vehicles in Entire 2x3 Network Grid: {active_vehs}")

            # Step 2: Compute AI Decisions for all 6 junctions
            decisions = {}
            print("\n2. DECENTRALIZED AI MODEL COMPUTATIONS & DECISIONS (Per Junction):")
            for j_id in junction_ids:
                counts = all_counts[j_id]
                chosen_dir, green_dur, scores = models[j_id].calculate_decision(counts)
                decisions[j_id] = (chosen_dir, green_dur, scores)
                
                score_str = f"N:{scores['N']} | E:{scores['E']} | S:{scores['S']} | W:{scores['W']}"
                print(f"   - [{j_id}] Scores ({score_str}) -> GRANT GREEN: {dir_names[chosen_dir]:5s} ({green_dur}s)")

            # Determine maximum green duration in this synchronized decision batch
            max_green_dur = max(d[1] for d in decisions.values())

            # Step 3: Apply signal transitions (yellow/all-red if changing phase)
            print(f"\n3. SIGNAL PHASE TRANSITIONS & GREEN EXECUTION (Max Cycle Window: {max_green_dur}s):")
            for j_id in junction_ids:
                chosen_dir, green_dur, _ = decisions[j_id]
                target_phase = get_target_phase(chosen_dir)
                current_phase = traci.trafficlight.getPhase(j_id)

                if current_phase != target_phase:
                    trans_phase = 1 if current_phase == 0 else 4
                    traci.trafficlight.setPhase(j_id, trans_phase)
                    traci.trafficlight.setPhaseDuration(j_id, 2.0)
                else:
                    traci.trafficlight.setPhase(j_id, target_phase)
                    traci.trafficlight.setPhaseDuration(j_id, float(green_dur))

            # Step transition for 2 seconds (20 steps at 0.1s step-length)
            print("   [SIGNAL TRANSITION] Executing 2s Yellow/All-Red Transition across grid...")
            for _ in range(20):
                traci.simulationStep()
                if gui:
                    time.sleep(0.03)

            # Activate Green phases for chosen directions
            for j_id in junction_ids:
                chosen_dir, green_dur, _ = decisions[j_id]
                target_phase = get_target_phase(chosen_dir)
                traci.trafficlight.setPhase(j_id, target_phase)
                traci.trafficlight.setPhaseDuration(j_id, float(green_dur))

            # Step simulation second by second for max_green_dur
            total_steps = int(max_green_dur * 10)
            sec_count = 0
            for s in range(total_steps):
                traci.simulationStep()
                if gui:
                    time.sleep(0.03)

                if (s + 1) % 10 == 0:
                    sec_count += 1
                    if sec_count % 3 == 0 or sec_count == max_green_dur:
                        print(f"   [RUNNING GRID GREEN] Grid Signal Active | Elapsed: {sec_count:2d}s / {max_green_dur}s | Active Vehs: {traci.vehicle.getIDCount()}")

            # Step 4: Show updated counts after cycle completion
            print(f"\n4. POST-EXECUTION VEHICLE COUNTS AFTER {max_green_dur}s CYCLE:")
            print("   " + "-" * 75)
            print("   Junction | North (N) | East (E)  | South (S) | West (W)  | Total Queue")
            print("   " + "-" * 75)
            for j_id in junction_ids:
                post_c = get_junction_counts(j_id)
                tot_q = sum(post_c.values())
                print(f"     {j_id:5s}  |  {post_c['N']:2d} vehs   |  {post_c['E']:2d} vehs   |  {post_c['S']:2d} vehs   |  {post_c['W']:2d} vehs   |   {tot_q:2d} vehs")
            print("   " + "-" * 75)

    except Exception as e:
        print(f"\n[ERROR] Simulation interrupted: {e}")
    finally:
        if gui:
            input("\n[PAUSED] Multi-Junction presentation view active. Press ENTER to close SUMO GUI...")
        traci.close()
        print("\n[OK] SUMO Multi-Junction Simulation closed cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo SUMO Multi-Junction Model Control")
    parser.add_argument("--gui", action="store_true", help="Launch SUMO GUI window")
    parser.add_argument("--cycles", type=int, default=10, help="Number of decision cycles")
    parser.add_argument("--cfg", type=str, default="sumo/multi_junction.sumocfg", help="Path to SUMO config file")
    args = parser.parse_args()

    run_multijunction_demo(gui=args.gui, cycles=args.cycles, cfg_path=args.cfg)
