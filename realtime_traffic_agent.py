# realtime_traffic_agent.py
"""
realtime_traffic_agent.py

This script collects real-time traffic congestion data for a 4-way intersection (e.g., Silk Board, Bangalore)
using the TomTom Traffic Flow API. If no API key is provided, it falls back to a time-of-day based congestion 
profile (simulating peak/off-peak traffic) to ensure a flawless live demo.

It computes traffic light signal decisions (phase and green duration) and updates the Flask web server.

Usage:
    python realtime_traffic_agent.py
"""

import time
import math
import requests
import datetime
import random

# -----------------------------
# CONFIGURATION & COORDINATES
# -----------------------------
# Let's target Silk Board Junction, Bangalore (12.9164, 77.6219)
# We define coordinates for points ~150 meters away in each direction:
COORDINATES = {
    "N": {"lat": 12.9180, "lng": 77.6219, "name": "Hosur Rd (Northbound)"},
    "E": {"lat": 12.9164, "lng": 77.6235, "name": "Outer Ring Rd (Eastbound)"},
    "S": {"lat": 12.9145, "lng": 77.6219, "name": "Hosur Rd (Southbound)"},
    "W": {"lat": 12.9164, "lng": 77.6200, "name": "Outer Ring Rd (Westbound)"}
}

# Optional: Add your TomTom API Key here.
# Get a free key at https://developer.tomtom.com/
TOMTOM_API_KEY = ""  # Leave empty to run in simulated live mode

FLASK_SERVER_URL = "http://127.0.0.1:5000/update"

# Traffic control heuristic parameters
PARAMS = {
    "S": 1.8,                  # vehicle clearance rate (veh/sec)
    "min_green": 8,
    "max_green": 45,
    "safety_buffer": 3,
    "cycle_target": 60,
    "max_wait_threshold": 60,  # starvation limit
    "alpha": 1.0,              # queue weight
    "beta": 0.6                # waiting time weight
}

# -----------------------------
# TRAFFIC API / SIMULATOR
# -----------------------------
def fetch_tomtom_congestion(lat, lng, api_key):
    """Fetch live traffic speed and calculate a congestion index from TomTom."""
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={api_key}&point={lat},{lng}"
    try:
        response = requests.get(url, timeout=3.0)
        if response.status_code == 200:
            data = response.json().get("flowSegmentData", {})
            current_speed = data.get("currentSpeed", 30)
            free_flow_speed = data.get("freeFlowSpeed", 50)
            
            # Congestion is the ratio of speed reduction
            congestion = max(0.0, 1.0 - (current_speed / max(1, free_flow_speed)))
            return congestion
    except Exception as e:
        print(f"[API ERROR] Failed to query TomTom for {lat},{lng}: {e}")
    return None

def get_simulated_congestion(lane):
    """
    Simulates real-world traffic profiles based on the current system time.
    Provides realistic peak hours (morning/evening commutes) for Bangalore roads.
    """
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    time_val = hour + (minute / 60.0)

    # 1. Morning Peak Hour (8:30 AM - 11:30 AM)
    if 8.5 <= time_val <= 11.5:
        # High traffic coming from South/North commuter corridors
        base_congestion = {"N": 0.85, "E": 0.40, "S": 0.90, "W": 0.45}
    # 2. Evening Peak Hour (5:00 PM - 8:30 PM)
    elif 17.0 <= time_val <= 20.5:
        # High traffic heading outwards to West/South corridors
        base_congestion = {"N": 0.50, "E": 0.80, "S": 0.95, "W": 0.85}
    # 3. Standard Daytime Traffic (11:30 AM - 5:00 PM)
    elif 11.5 < time_val < 17.0:
        base_congestion = {"N": 0.55, "E": 0.45, "S": 0.60, "W": 0.50}
    # 4. Late Night / Early Morning (10:00 PM - 7:00 AM)
    else:
        base_congestion = {"N": 0.10, "E": 0.08, "S": 0.12, "W": 0.07}

    # Add small random noise to make the queues fluctuate realistically
    noise = random.uniform(-0.05, 0.05)
    congestion = max(0.0, min(1.0, base_congestion[lane] + noise))
    return congestion

def get_lane_queue(lane):
    """Gets the congestion level (0-1) and scales it to a queue count (0-30)."""
    if TOMTOM_API_KEY:
        coords = COORDINATES[lane]
        congestion = fetch_tomtom_congestion(coords["lat"], coords["lng"], TOMTOM_API_KEY)
        if congestion is not None:
            print(f"[API] Fetched live data for {lane} ({coords['name']}): Congestion = {congestion:.2%}")
            return int(congestion * 30)
        else:
            print(f"[FALLBACK] API failed. Using simulated profile for {lane}.")
            
    # Fallback/Simulated mode
    congestion = get_simulated_congestion(lane)
    print(f"[SIMULATED] Profile for {lane}: Congestion = {congestion:.2%}")
    return int(congestion * 30)

# -----------------------------
# TRAFFIC CONTROL DECISION
# -----------------------------
def choose_phase_and_green(queues, last_served):
    """Computes scores using queue lengths and waiting times to select green phase."""
    alpha = PARAMS["alpha"]
    beta = PARAMS["beta"]
    max_wait = PARAMS["max_wait_threshold"]

    # Starvation check (forced service if wait time exceeds limit)
    for d in ["N", "E", "S", "W"]:
        if last_served.get(d, 0) >= max_wait and queues.get(d, 0) > 0:
            print(f"[STARVATION PREVENTED] Forcing green for {d} due to starvation threshold.")
            chosen = d
            break
    else:
        # Score calculation
        scores = {
            d: alpha * queues[d] + beta * last_served[d]
            for d in ["N", "E", "S", "W"]
        }
        chosen = max(scores, key=scores.get)

    q = queues[chosen]
    clear_t = q / PARAMS["S"] if PARAMS["S"] > 0 else 0
    green = math.ceil(clear_t) + PARAMS["safety_buffer"]
    
    # Clamp to boundaries
    green = max(PARAMS["min_green"], min(PARAMS["max_green"], green))
    return chosen, green

# -----------------------------
# MAIN SERVICE LOOP
# -----------------------------
def main():
    print("=" * 60)
    print("🚦 TRAFFIX: REAL-TIME TRAFFIC COLLECTION AGENT")
    print(f"Target Intersection: Silk Board Junction, Bangalore")
    if TOMTOM_API_KEY:
        print("[MODE] Real-Time TomTom API Mode Active")
    else:
        print("[MODE] Simulated Live Mode Active (profile based on local time)")
    print("=" * 60)

    last_served = {"N": 0, "E": 0, "S": 0, "W": 0}

    while True:
        # 1. Fetch queues for all roads
        print(f"\n--- Update Cycle: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        counts = {lane: get_lane_queue(lane) for lane in ["N", "E", "S", "W"]}
        
        # 2. Decide the green lane and timing
        phase, green = choose_phase_and_green(counts, last_served)
        print(f"[DECISION] Active Green: {phase} | Timing: {green} seconds")

        # 3. Post to Flask Web Server (which updates dashboard.py and templates/index.html)
        try:
            payload = {
                "N": counts["N"],
                "E": counts["E"],
                "S": counts["S"],
                "W": counts["W"],
                "green_lane": phase,
                "green_time": green
            }
            r = requests.post(FLASK_SERVER_URL, json=payload, timeout=2.0)
            if r.status_code == 200:
                print(f"[UPLOAD] Server updated successfully.")
            else:
                print(f"[UPLOAD FAILED] Server responded with status: {r.status_code}")
        except Exception as e:
            print(f"[CONNECTION ERROR] Cannot upload to Flask server: {e}. (Make sure 'traffic_server.py' is running!)")

        # 4. Update wait times for next cycle
        for lane in ["N", "E", "S", "W"]:
            if lane == phase:
                last_served[lane] = 0
            else:
                last_served[lane] += green

        # 5. Wait for the green cycle duration to simulate real-time operations
        print(f"Waiting {green}s for signal execution...")
        time.sleep(green)

if __name__ == "__main__":
    main()
