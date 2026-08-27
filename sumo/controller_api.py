# controller_api.py
from flask import Flask, request, jsonify
import math, threading, time, logging

app = Flask(__name__)

# -------------------------
# Parameters (tune as needed)
# -------------------------
PARAMS = {
    "S": 1.8,
    "min_green": 6,
    "max_green": 45,
    "safety_buffer": 2,
    "cycle_target": 60,
    "max_wait_threshold": 120,
    "alpha": 1.0,
    "beta": 0.6
}

# -------------------------
# Multi-Junction Controller State
# -------------------------
lock = threading.Lock()
MAX_REPEAT = 2   # when same chosen > MAX_REPEAT times, force rotation

class JunctionState:
    def __init__(self, j_id):
        self.j_id = j_id
        self.last_served = {"N": 0, "E": 0, "S": 0, "W": 0}
        self.last_chosen = None
        self.repeat_count = 0
        self.last_counts = {"N": 0, "E": 0, "S": 0, "W": 0}
        self.last_decision = {}

junction_registry = {}

def get_or_create_junction_state(j_id):
    if j_id not in junction_registry:
        junction_registry[j_id] = JunctionState(j_id)
    return junction_registry[j_id]

# -------------------------
# Helper utilities
# -------------------------
def _age_last_served_for_junction(j_state, seconds):
    """Increase last_served timers by seconds (called when we serve for 'green' seconds)."""
    for d in j_state.last_served:
        j_state.last_served[d] += seconds

def local_heuristic(queues, j_state):
    """
    Compute a score for each direction and choose the best for a specific junction.
    Returns: chosen_dir, green_seconds, scores_dict
    """
    # priority scores = alpha * queue + beta * waiting_time
    scores = {d: PARAMS["alpha"] * queues.get(d, 0) + PARAMS["beta"] * j_state.last_served.get(d, 0) for d in ["N", "E", "S", "W"]}
    # choose best
    chosen = max(scores, key=scores.get)
    q = queues.get(chosen, 0)
    clear_t = q / PARAMS["S"] if PARAMS["S"] > 0 else 0
    G = math.ceil(clear_t) + PARAMS["safety_buffer"]

    total_q = sum(queues.values())
    if total_q > 0 and q < 2:
        # proportional fallback
        prop = q / max(1, total_q)
        G = max(1, int(round(prop * PARAMS["cycle_target"])))
    G = max(PARAMS["min_green"], min(PARAMS["max_green"], G))
    return chosen, int(G), scores

def process_decision_for_junction(j_id, queues):
    with lock:
        j_state = get_or_create_junction_state(j_id)
        j_state.last_counts = queues

        chosen, green, scores = local_heuristic(queues, j_state)

        # rotation guard to avoid repeated serving
        if j_state.last_chosen == chosen:
            j_state.repeat_count += 1
        else:
            j_state.repeat_count = 0

        if j_state.repeat_count > MAX_REPEAT:
            sorted_dirs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for d, sc in sorted_dirs:
                if d != j_state.last_chosen:
                    chosen = d
                    green = max(PARAMS["min_green"], int(round(green // 2)))
                    app.logger.info(f"[{j_id}] Rotation guard triggered: forcing {chosen} for {green}s")
                    break
            j_state.repeat_count = 0

        # update last_served
        _age_last_served_for_junction(j_state, green)
        j_state.last_served[chosen] = 0
        j_state.last_chosen = chosen

        now_ts = time.time()
        decision = {
            "junction": j_id,
            "phase": chosen,
            "green": int(green),
            "start_time": now_ts,
            "end_time": now_ts + green
        }
        j_state.last_decision = decision
        app.logger.info(f"[{j_id}] Decision made: {chosen} for {green}s | queues={queues} | scores={scores}")
        return decision

# -------------------------
# API Endpoints
# -------------------------
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Smart Traffic Controller API is running."})

@app.route("/decide", methods=["POST"])
def decide():
    data = request.get_json(force=True)

    # Batch multi-junction request
    if "junctions" in data:
        decisions = {}
        for j_id, j_data in data["junctions"].items():
            queues = j_data.get("counts", {"N": 0, "E": 0, "S": 0, "W": 0})
            dec = process_decision_for_junction(j_id, queues)
            decisions[j_id] = dec
        return jsonify({"decisions": decisions})

    # Single junction request (supports both single junction 'C' and specific multi-junction 'J1', 'J2', etc.)
    j_id = data.get("junction", "default")
    queues = data.get("counts", {"N": 0, "E": 0, "S": 0, "W": 0})
    decision = process_decision_for_junction(j_id, queues)
    return jsonify({"phase": decision["phase"], "green": decision["green"], "junction": j_id})

@app.route("/get_status", methods=["GET"])
@app.route("/status", methods=["GET"])
def get_status():
    with lock:
        # Aggregated queues
        total_counts = {"N": 0, "E": 0, "S": 0, "W": 0}
        j_data = {}
        last_dec = {}
        for j_id, j_state in junction_registry.items():
            for d in ["N", "E", "S", "W"]:
                total_counts[d] += j_state.last_counts.get(d, 0)
            j_data[j_id] = {
                "counts": j_state.last_counts,
                "last_decision": j_state.last_decision,
                "last_served": j_state.last_served
            }
            if j_state.last_decision:
                last_dec = j_state.last_decision

        return jsonify({
            "timestamp": time.time(),
            "counts": total_counts,
            "junctions": j_data,
            "last_decision": last_dec
        })

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000)
