# verify_multi_junction.py
import threading
import time
import requests
import traci
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import controller_api
import rl_infer
from sumo_bridge import JUNCTION_LANE_MAP, JunctionControllerState, dir_to_phase, get_all_red_phase, get_lane_counts, request_decision

def run_end_to_end_test():
    print("========================================================")
    print("   SUMO MULTI-JUNCTION COMPREHENSIVE END-TO-END TEST    ")
    print("========================================================")

    # 1. Start Controller API in background thread
    server_thread = threading.Thread(
        target=lambda: controller_api.app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    time.sleep(1.0)

    # Verify API
    try:
        r_health = requests.get('http://127.0.0.1:5000/health', timeout=1.0)
        api_health_ok = (r_health.status_code == 200 and r_health.json().get('status') == 'ok')
        print(f"[TEST] Controller API Health Check: {'PASS' if api_health_ok else 'FAIL'}")
    except Exception as e:
        print(f"[TEST] Controller API Health Check: FAIL ({e})")
        api_health_ok = False

    # 2. Test RL inference with multi-junction inputs
    rl_test_ok = True
    for j in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']:
        dec = rl_infer.rl_decide({'N': 5, 'E': 10, 'S': 2, 'W': 1}, junction_id=j)
        if 'phase' not in dec or 'green' not in dec:
            rl_test_ok = False
    print(f"[TEST] Decentralized RL Inference Check: {'PASS' if rl_test_ok else 'FAIL'}")

    # 3. Start SUMO TraCI
    sumo_cmd = ['sumo', '-c', 'multi_junction.sumocfg']
    traci.start(sumo_cmd)
    tls_list = list(traci.trafficlight.getIDList())
    print(f"[TEST] SUMO TraCI Connection: PASS (Found TLS: {tls_list})")

    # 4. Step Simulation and track metrics
    phase_history = {tls: set() for tls in tls_list}
    vehicle_history = {}
    states = {tls: JunctionControllerState(tls) for tls in tls_list}

    # Tracking vehicle positions for visualization
    sample_veh_positions = []

    print("[INFO] Simulating 1000 steps (100.0s simulation time)...")
    for step in range(1000):
        traci.simulationStep()
        sim_time = traci.simulation.getTime()

        # Step Traffic Light controllers
        for j_id, state in states.items():
            current_phase = traci.trafficlight.getPhase(j_id)
            phase_history[j_id].add(current_phase)
            counts = get_lane_counts(j_id)
            num_phases = len(traci.trafficlight.getAllProgramLogics(j_id)[0].phases)

            if state.all_red_active:
                if sim_time >= state.all_red_end:
                    state.all_red_active = False
                else:
                    continue

            if state.green_active and sim_time >= state.green_end_time:
                all_red_p = get_all_red_phase(state.current_phase_idx, num_phases)
                try:
                    traci.trafficlight.setPhase(j_id, all_red_p)
                    traci.trafficlight.setPhaseDuration(j_id, state.all_red_duration)
                except Exception:
                    pass
                state.all_red_active = True
                state.all_red_end = sim_time + state.all_red_duration
                state.green_active = False
                continue

            if not state.green_active:
                dec = request_decision(j_id, counts)
                chosen = dec.get('phase', 'N')
                green = int(dec.get('green', 10))
                p_idx = dir_to_phase(chosen, num_phases)
                traci.trafficlight.setPhase(j_id, p_idx)
                traci.trafficlight.setPhaseDuration(j_id, green)
                state.green_active = True
                state.green_end_time = sim_time + green
                state.current_phase_idx = p_idx
                state.chosen = chosen

        # Track active vehicles
        active_vehs = traci.vehicle.getIDList()
        if step == 500:
            # Capture positions for visualization at step 500
            for vid in active_vehs:
                x, y = traci.vehicle.getPosition(vid)
                sample_veh_positions.append((vid, x, y))

        for vid in active_vehs:
            speed = traci.vehicle.getSpeed(vid)
            edge = traci.vehicle.getRoadID(vid)
            if vid not in vehicle_history:
                vehicle_history[vid] = {
                    'edges': [],
                    'speeds': [],
                    'stopped_at_red': False,
                    'moved_at_green': False,
                    'junctions_visited': set()
                }

            if edge and (not vehicle_history[vid]['edges'] or vehicle_history[vid]['edges'][-1] != edge):
                vehicle_history[vid]['edges'].append(edge)
                for j in ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']:
                    if j in edge:
                        vehicle_history[vid]['junctions_visited'].add(j)

            vehicle_history[vid]['speeds'].append(speed)

            if speed < 0.1 and not edge.startswith(':'):
                vehicle_history[vid]['stopped_at_red'] = True

            if speed > 4.0 and vehicle_history[vid]['stopped_at_red']:
                vehicle_history[vid]['moved_at_green'] = True

    # 5. Dashboard / Status verification
    try:
        r_status = requests.get('http://127.0.0.1:5000/get_status', timeout=1.0)
        status_data = r_status.json()
        dashboard_ok = (r_status.status_code == 200 and len(status_data.get('junctions', {})) == 6)
        print(f"[TEST] Live Dashboard API Status Check: {'PASS' if dashboard_ok else 'FAIL'}")
    except Exception as e:
        dashboard_ok = False
        print(f"[TEST] Live Dashboard API Status Check: FAIL ({e})")

    # 6. Evaluation metrics
    spawned_count = len(vehicle_history)
    stopped_count = sum(1 for v in vehicle_history.values() if v['stopped_at_red'])
    moved_count = sum(1 for v in vehicle_history.values() if v['stopped_at_red'] and v['moved_at_green'])
    multi_j_vehs = [v for v, data in vehicle_history.items() if len(data['junctions_visited']) >= 2]
    all_tl_changed = all(len(phases) >= 2 for phases in phase_history.values())

    print("\n----------------- VERIFICATION METRICS -----------------")
    print(f"Total Vehicles Spawned:                {spawned_count}")
    print(f"Vehicles Stopped at Red Signal:        {stopped_count}")
    print(f"Vehicles Moved on Green After Stop:    {moved_count}")
    print(f"Vehicles Traversing >= 2 Junctions:    {len(multi_j_vehs)}")
    print(f"Traffic Lights with Active Changes:    { {k: list(v) for k, v in phase_history.items()} }")

    # Trace 3 exemplary multi-junction vehicles
    print("\n----------------- DETAILED MULTI-JUNCTION TRACES -----------------")
    for vid in multi_j_vehs[:3]:
        data = vehicle_history[vid]
        print(f"Vehicle ID: {vid}")
        print(f"  - Junctions Visited: {sorted(list(data['junctions_visited']))}")
        print(f"  - Edge Path:         {' -> '.join(data['edges'])}")
        print(f"  - Obeyed Red/Green:  Stopped={data['stopped_at_red']}, Resumed={data['moved_at_green']}")

    traci.close()

    # 7. Render Visual Map of the Multi-Junction Simulation
    plt.figure(figsize=(10, 8))
    # Junction coordinates
    coords = {
        'J1': (300, 600), 'J2': (600, 600), 'J3': (900, 600),
        'J4': (300, 300), 'J5': (600, 300), 'J6': (900, 300),
        'N1': (300, 900), 'N2': (600, 900), 'N3': (900, 900),
        'S1': (300, 0),   'S2': (600, 0),   'S3': (900, 0),
        'W1': (0, 600),   'W2': (0, 300),
        'E1': (1200, 600),'E2': (1200, 300)
    }

    # Draw roads
    road_links = [
        ('W1', 'J1'), ('J1', 'J2'), ('J2', 'J3'), ('J3', 'E1'),
        ('W2', 'J4'), ('J4', 'J5'), ('J5', 'J6'), ('J6', 'E2'),
        ('N1', 'J1'), ('J1', 'J4'), ('J4', 'S1'),
        ('N2', 'J2'), ('J2', 'J5'), ('J5', 'S2'),
        ('N3', 'J3'), ('J3', 'J6'), ('J6', 'S3')
    ]

    for u, v in road_links:
        x1, y1 = coords[u]
        x2, y2 = coords[v]
        plt.plot([x1, x2], [y1, y2], color='#333333', linewidth=8, solid_capstyle='round', zorder=1)
        plt.plot([x1, x2], [y1, y2], color='#ffffff', linestyle='--', linewidth=1.5, zorder=2)

    # Draw nodes
    for name, (x, y) in coords.items():
        if name.startswith('J'):
            plt.scatter(x, y, s=400, color='#e74c3c', edgecolors='black', linewidth=2, zorder=5)
            plt.text(x, y+25, f"{name} (TL)", fontsize=11, fontweight='bold', ha='center', color='#c0392b')
        else:
            plt.scatter(x, y, s=150, color='#3498db', edgecolors='black', linewidth=1.5, zorder=4)
            plt.text(x, y+20, name, fontsize=9, ha='center', color='#2980b9')

    # Draw sampled vehicles
    if sample_veh_positions:
        vx = [p[1] for p in sample_veh_positions]
        vy = [p[2] for p in sample_veh_positions]
        plt.scatter(vx, vy, s=40, color='#f1c40f', edgecolors='black', linewidth=0.8, label=f'Active Vehicles (t=50s, n={len(sample_veh_positions)})', zorder=6)

    plt.title("SUMO Multi-Junction Traffic Network (2x3 Interconnected Grid)", fontsize=14, fontweight='bold')
    plt.xlabel("X Coordinate (m)")
    plt.ylabel("Y Coordinate (m)")
    plt.legend(loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig("multi_junction_network_view.png", dpi=150)
    plt.close()
    print("[INFO] Network simulation visualization saved to 'multi_junction_network_view.png'.")

    print("========================================================")
    print("               VERIFICATION COMPLETED                   ")
    print("========================================================")

if __name__ == '__main__':
    run_end_to_end_test()
