"""
traffic_monitor.py

- Monitors 4 videos (N, E, S, W).
- Counts vehicles per direction.
- Sends counts to traffic controller API.
- Gets phase decision and green time.
- Stops automatically when all videos end.
"""

import cv2
import requests
import time

# -----------------------------
# Video files (replace with your files)
# -----------------------------
video_files = {
    "N": "1900-151662242_medium.mp4",
    "E": "131232-749706873_small.mp4",
    "S": "27260-362770008_small.mp4",
    "W": "west.mp4"
}

# -----------------------------
# Initialize video captures
# -----------------------------
caps = {dir: cv2.VideoCapture(fname) for dir, fname in video_files.items()}

# -----------------------------
# Vehicle counting (simple simulation)
# -----------------------------
vehicle_counts = {"N":0, "E":0, "S":0, "W":0}
last_served = {"N":0, "E":0, "S":0, "W":0}

# For simulation, we assume 1 new vehicle per frame per direction
# Replace with your actual detection model if needed

# -----------------------------
# Controller API
# -----------------------------
API_URL = "http://127.0.0.1:5000/decide"

# -----------------------------
# Main loop
# -----------------------------
all_done = False

while not all_done:
    all_done = True  # assume done until we find a video still running
    
    # read frames from all videos
    for dir, cap in caps.items():
        ret, frame = cap.read()
        if ret:
            all_done = False
            # simulate vehicle detection: add 0-1 vehicles per frame randomly
            import random
            vehicle_counts[dir] += random.randint(0,1)
        # else: video ended for this direction
    
    if not all_done:
        # send counts to controller API
        try:
            payload = {"counts": vehicle_counts, "last_served": last_served}
            resp = requests.post(API_URL, json=payload)
            data = resp.json()
            phase = data.get("phase")
            green = data.get("green")
            print(f"Phase: {phase}, Green time: {green}s, Counts: {vehicle_counts}")
            # update last_served
            for d in last_served.keys():
                if d == phase:
                    last_served[d] = 0
                    vehicle_counts[d] = max(vehicle_counts[d] - green, 0)  # vehicles cleared
                else:
                    last_served[d] += green
        except Exception as e:
            print("API request failed:", e)
        
        time.sleep(1)  # simulate 1s per tick

# release all videos
for cap in caps.values():
    cap.release()

print("All videos finished. Traffic monitoring stopped.")
