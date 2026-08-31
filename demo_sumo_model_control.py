"""
demo_sumo_model_control.py

Adaptive SUMO Traffic Control System for Live Presentation:
1. Displays line-by-line vehicle counts for EVERY approach (North, East, South, West).
2. Calculates priority scores and exact required green time for the highest demand direction.
3. Strictly enforces the green duration countdown while vehicles physically move across the junction.
4. Transitions smoothly to the next direction with natural traffic flow (no gridlock flooding).
"""

import os
import sys
import time
import argparse
import numpy as np
import traci


# -------------------------------------------------------------
# 1. AI Traffic Control Model
# -------------------------------------------------------------
class SmartTrafficModel:
    """
    Evaluates traffic demand per lane:
    Priority Score = Queue_Length + 0.6 * Wait_Time
    Calculates exact required green duration (8s to 25s) based on queue size.
    """
    def __init__(self):
        self.directions = ["N", "E", "S", "W"]
        self.last_served = {"N": 0, "E": 0, "S": 0, "W": 0}
        self.alpha = 1.0  # Weight for vehicle queue count
        self.beta = 0.6   # Weight for waiting time (prevents starvation)

    def calculate_decision(self, counts):
        # 1. Compute priority score for each direction
        scores = {}
        for d in self.directions:
            q = counts.get(d, 0)
            w = self.last_served.get(d, 0)
            scores[d] = round(self.alpha * q + self.beta * w, 1)

        # 2. Select direction with maximum priority score
        chosen_dir = max(scores, key=scores.get)
        target_queue = counts.get(chosen_dir, 0)

        # 3. Calculate exact required green duration
        # Clear rate ~1.8 vehicles/sec + 3s safety margin
        if target_queue == 0:
            green_duration = 8
        else:
            clear_time = int(np.ceil(target_queue / 1.8)) + 3
            green_duration = max(8, min(25, clear_time))

        # 4. Update wait timers
        for d in self.directions:
            if d == chosen_dir:
                self.last_served[d] = 0
            else:
                self.last_served[d] += green_duration + 2  # Include 2s transition

        return chosen_dir, green_duration, scores


# -------------------------------------------------------------
# 2. Helper Functions
# -------------------------------------------------------------
def get_lane_counts(tls_id="C"):
    """Fetches exact vehicle counts for North, East, South, and West approaches."""
    lane_map = {
        "N": ["NtoC_0", "NtoC_1"],
        "E": ["EtoC_0", "EtoC_1"],
        "S": ["StoC_0", "StoC_1"],
        "W": ["WtoC_0", "WtoC_1"],
    }
    counts = {}
    for d, lanes in lane_map.items():
        total = 0
        for l in lanes:
            try:
                total += traci.lane.getLastStepVehicleNumber(l)
            except Exception:
                pass
        counts[d] = total
    return counts


def execute_strict_green_signal(tls_id, direction, green_duration, gui_mode=False):
    """
    Strictly executes the signal phase for the exact requested green_duration.
    
    SUMO Phase Map (tl.add.xml):
      Phase 0: North-South Green
      Phase 1: All-Red Transition (from NS)
      Phase 2: East-West Green
      Phase 3: All-Red Transition (from EW)
    """
    target_phase = 2 if direction in ["E", "W"] else 0
    current_phase = traci.trafficlight.getPhase(tls_id)

    # 1. Transition to Yellow/All-Red if changing direction
    if current_phase != target_phase:
        transition_phase = 1 if current_phase == 0 else 3
        print(f"   [SIGNAL TRANSITION] Yellow/All-Red (Phase {transition_phase}) -> 2 Seconds Transition...")
        traci.trafficlight.setPhase(tls_id, transition_phase)
        traci.trafficlight.setPhaseDuration(tls_id, 2.0)
        
        # 2 seconds = 20 simulation steps (at 0.1s step-length)
        for _ in range(20):
            traci.simulationStep()
            if gui_mode:
                time.sleep(0.04)

    # 2. Activate GREEN Signal for chosen direction
    direction_labels = {"N": "NORTH", "E": "EAST", "S": "SOUTH", "W": "WEST"}
    dir_name = direction_labels.get(direction, direction)
    
    print(f"\n   ==========================================================")
    print(f"   >>> [GREEN LIGHT ACTIVE]: {dir_name} DIRECTION <<<")
    print(f"   >>> STRICT GREEN DURATION: {green_duration} SECONDS <<<")
    print(f"   ==========================================================")
    
    traci.trafficlight.setPhase(tls_id, target_phase)
    traci.trafficlight.setPhaseDuration(tls_id, float(green_duration))

    # Total simulation steps (step_length = 0.1s -> 10 steps per second)
    total_steps = int(green_duration * 10)
    
    # 3. Strictly hold green signal second by second
    sec_count = 0
    for s in range(total_steps):
        traci.simulationStep()
        if gui_mode:
            time.sleep(0.04)  # Smooth presentation speed
        
        # Log progress every 1 second (10 steps)
        if (s + 1) % 10 == 0:
            sec_count += 1
            rem = green_duration - sec_count
            print(f"   [RUNNING GREEN SIGNAL] {dir_name} Green Active | Elapsed: {sec_count}s | Remaining: {rem}s")


# -------------------------------------------------------------
# 3. Main Run Function
# -------------------------------------------------------------
def run_demo(gui=False, cycles=10, cfg_path="sumo/4way.sumocfg"):
    if not os.path.exists(cfg_path):
        if os.path.exists("4way.sumocfg"):
            cfg_path = "4way.sumocfg"
        else:
            print(f"Error: SUMO config file '{cfg_path}' not found.")
            return

    cmd = "sumo-gui" if gui else "sumo"
    print("=" * 80)
    print("      [SMART TRAFFIC MANAGEMENT SYSTEM] -- AI SIGNAL CONTROL DEMO")
    print("=" * 80)
    print(f" Executing via: {'SUMO GUI Visual Window' if gui else 'Headless Console'}")
    print(f" Configuration: {cfg_path}")
    print("=" * 80)

    traci.start([cmd, "-c", cfg_path, "--start", "--quit-on-end"])
    print("\n[OK] SUMO TraCI initialized successfully.")

    # Instantiate AI Controller
    model = SmartTrafficModel()

    # Warm-up simulation for 3 seconds so natural traffic reaches the intersection
    print("[INIT] Spawning natural traffic flow across all 4 directions...")
    for _ in range(30):
        traci.simulationStep()

    try:
        for cycle in range(1, cycles + 1):
            sim_time = traci.simulation.getTime()
            active_vehs = traci.vehicle.getIDCount()

            print("\n" + "=" * 80)
            print(f"  DECISION CYCLE {cycle} OF {cycles}  |  SUMO Simulation Time: {sim_time:.1f}s")
            print("=" * 80)
            
            # Step 1: Read and display vehicle counts of EVERY line/approach
            counts = get_lane_counts("C")
            print(f"\n1. REAL-TIME VEHICLE COUNTS PER APPROACH:")
            print(f"   -----------------------------------------")
            print(f"   - NORTH Approach (N) : {counts['N']:2d} vehicles")
            print(f"   - EAST  Approach (E) : {counts['E']:2d} vehicles")
            print(f"   - SOUTH Approach (S) : {counts['S']:2d} vehicles")
            print(f"   - WEST  Approach (W) : {counts['W']:2d} vehicles")
            print(f"   -----------------------------------------")
            print(f"   Total Active Vehicles in Network: {active_vehs}")

            # Step 2: Calculate Priority Scores and Decide Green Signal Direction & Time
            chosen_dir, green_duration, scores = model.calculate_decision(counts)
            
            print(f"\n2. AI MODEL COMPUTATION & DECISION:")
            print(f"   - Calculated Priority Scores (Queue + 0.6 * Wait):")
            print(f"     North: {scores['N']} | East: {scores['E']} | South: {scores['S']} | West: {scores['W']}")
            
            dir_names = {"N": "NORTH", "E": "EAST", "S": "SOUTH", "W": "WEST"}
            print(f"\n   >>> MODEL DECISION: GRANT GREEN TO {dir_names[chosen_dir]} APPROACH <<<")
            print(f"   >>> CALCULATED GREEN DURATION: {green_duration} SECONDS <<<")

            # Step 3: Strictly enforce green signal duration while vehicles cross
            execute_strict_green_signal("C", chosen_dir, green_duration, gui_mode=gui)

            # Step 4: Show updated counts after exact signal completion
            post_counts = get_lane_counts("C")
            print(f"\n4. VEHICLE COUNTS AFTER {green_duration}s GREEN SIGNAL EXECUTION:")
            print(f"   North: {post_counts['N']} | East: {post_counts['E']} | South: {post_counts['S']} | West: {post_counts['W']}")

    except Exception as e:
        print(f"\n[ERROR] Simulation interrupted: {e}")
    finally:
        if gui:
            input("\n[PAUSED] Presentation view active. Press ENTER to close SUMO GUI...")
        traci.close()
        print("\n[OK] SUMO Simulation closed cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo SUMO Model Control")
    parser.add_argument("--gui", action="store_true", help="Launch SUMO GUI window")
    parser.add_argument("--cycles", type=int, default=10, help="Number of decision cycles")
    parser.add_argument("--multijunction", action="store_true", help="Run multi-junction 2x3 network demo")
    parser.add_argument("--cfg", type=str, default="sumo/4way.sumocfg", help="SUMO config file path")
    args = parser.parse_args()

    if args.multijunction or "multi_junction" in args.cfg:
        from demo_multijunction_model_control import run_multijunction_demo
        run_multijunction_demo(gui=args.gui, cycles=args.cycles, cfg_path=args.cfg if "multi_junction" in args.cfg else "sumo/multi_junction.sumocfg")
    else:
        run_demo(gui=args.gui, cycles=args.cycles, cfg_path=args.cfg)
