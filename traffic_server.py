# traffic_server.py
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app) # Allow cross-origin requests from React dashboard

# -------------------------
# GLOBAL STATE
# -------------------------
traffic_state = {
    "counts": {"N": 0, "E": 0, "S": 0, "W": 0},
    "green_lane": "N",
    "green_time": 10,
    "green_end": time.time() + 10
}

# -------------------------
# UPDATE FROM YOLO / RL
# -------------------------
@app.route("/update", methods=["POST"])
def update_from_yolo():
    data = request.get_json()

    traffic_state["counts"] = {
        "N": int(data.get("N", 0)),
        "E": int(data.get("E", 0)),
        "S": int(data.get("S", 0)),
        "W": int(data.get("W", 0))
    }

    traffic_state["green_lane"] = data.get("green_lane", "N")
    traffic_state["green_time"] = int(data.get("green_time", 10))
    traffic_state["green_end"] = time.time() + traffic_state["green_time"]

    return jsonify({"status": "updated"})

# -------------------------
# API FOR UI (poll every 1s)
# -------------------------
@app.route("/status")
def status():
    remaining = max(0, int(traffic_state["green_end"] - time.time()))
    return jsonify({
        "counts": traffic_state["counts"],
        "green_lane": traffic_state["green_lane"],
        "green_remaining": remaining
    })

# -------------------------
# LANDING PAGE
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
