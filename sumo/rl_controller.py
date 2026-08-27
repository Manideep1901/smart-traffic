# rl_controller.py
# RL DQN agent that controls SUMO traffic lights via TraCI.
import os
import random
import time
from collections import deque, namedtuple
import argparse

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import traci

# ----------------------------
# CONFIG & Topology
# ----------------------------
JUNCTION_LANE_MAP = {
    "C": {
        "N": ["NtoC_0", "NtoC_1"],
        "E": ["EtoC_0", "EtoC_1"],
        "S": ["StoC_0", "StoC_1"],
        "W": ["WtoC_0", "WtoC_1"],
    },
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

STEP_SLEEP = 0.0     # pause per sim step
DT = 1.0             # agent decision timestep (seconds)

# Action space: (direction, green seconds)
DIRECTIONS = ["N", "E", "S", "W"]
GREEN_CHOICES = [6, 10, 15, 20]   # discrete green durations
ACTIONS = [(d, g) for d in DIRECTIONS for g in GREEN_CHOICES]
N_ACTIONS = len(ACTIONS)

# RL hyperparams
STATE_SIZE = 4
GAMMA = 0.99
LR = 1e-3
BATCH_SIZE = 64
BUFFER_CAPACITY = 20000
MIN_REPLAY_SIZE = 500
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 10000  # steps
TARGET_UPDATE = 1000  # steps
MAX_TRAIN_STEPS = 80000

MODEL_SAVE_PATH = "dqn_sumo_model.pth"

# ----------------------------
# NETWORK / DQN
# ----------------------------
class QNetwork(nn.Module):
    def __init__(self, state_size, n_actions, hidden=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_actions)
        )

    def forward(self, x):
        return self.net(x)

Transition = namedtuple("Transition", ("state", "action", "reward", "next_state", "done"))

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, *args):
        self.buffer.append(Transition(*args))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))

    def __len__(self):
        return len(self.buffer)

# ----------------------------
# Helpers: SUMO ↔ State/Action/Reward
# ----------------------------
def read_lane_counts(tls_id="C"):
    lanes = JUNCTION_LANE_MAP.get(tls_id, {})
    counts = {}
    for d in ["N", "E", "S", "W"]:
        lane_list = lanes.get(d, [])
        total = 0
        for l in lane_list:
            try:
                total += traci.lane.getLastStepVehicleNumber(l)
            except Exception:
                pass
        counts[d] = total
    return counts

def state_from_counts(counts):
    """Return numpy array [N, E, S, W]."""
    return np.array([counts[d] for d in ["N", "E", "S", "W"]], dtype=np.float32)

def apply_action(action_idx, tls_id="C"):
    """Set SUMO trafficlight phase for chosen direction and return green duration."""
    direction, green = ACTIONS[action_idx]
    num_phases = len(traci.trafficlight.getAllProgramLogics(tls_id)[0].phases) if traci.trafficlight.getAllProgramLogics(tls_id) else 6
    if num_phases == 6:
        phase_index = 0 if direction in ("N", "S") else 3
    else:
        phase_index = 0 if direction in ("N", "S") else 2

    try:
        traci.trafficlight.setPhase(tls_id, phase_index)
        traci.trafficlight.setPhaseDuration(tls_id, green)
    except Exception as e:
        pass
    return direction, green

def accumulate_reward_during_green(green_seconds, tls_ids):
    """
    Step SUMO for green_seconds (in simulation seconds) and compute reward.
    Reward = negative total queue length across controlled junctions.
    """
    total_reward = 0.0
    steps = max(1, int(round(green_seconds / DT)))
    for _ in range(steps):
        traci.simulationStep()
        if STEP_SLEEP:
            time.sleep(STEP_SLEEP)
        for tls in tls_ids:
            counts = read_lane_counts(tls)
            total_reward += -sum(counts.values())
    return total_reward

# ----------------------------
# DQN TRAIN / EVAL
# ----------------------------
def select_action(state, policy_net, steps_done):
    eps_threshold = EPS_END + (EPS_START - EPS_END) * max(0.0, (1 - steps_done / EPS_DECAY))
    if random.random() < eps_threshold:
        return random.randrange(N_ACTIONS)
    else:
        with torch.no_grad():
            state_v = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            qvals = policy_net(state_v).cpu().numpy()[0]
            return int(np.argmax(qvals))

def optimize_model(policy_net, target_net, optimizer, replay_buffer):
    if len(replay_buffer) < BATCH_SIZE:
        return
    trans = replay_buffer.sample(BATCH_SIZE)
    states = torch.tensor(np.array(trans.state), dtype=torch.float32)
    actions = torch.tensor(trans.action, dtype=torch.int64).unsqueeze(1)
    rewards = torch.tensor(trans.reward, dtype=torch.float32).unsqueeze(1)
    next_states = torch.tensor(np.array(trans.next_state), dtype=torch.float32)
    dones = torch.tensor(trans.done, dtype=torch.float32).unsqueeze(1)

    q_values = policy_net(states).gather(1, actions)
    with torch.no_grad():
        next_q = target_net(next_states).max(1)[0].unsqueeze(1)
        target = rewards + (1 - dones) * GAMMA * next_q

    loss = nn.functional.mse_loss(q_values, target)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

# ----------------------------
# MAIN: train or run
# ----------------------------
def train_or_run(train=True, n_steps=20000, sumo_cfg="multi_junction.sumocfg", gui=False):
    device = torch.device("cpu")
    policy_net = QNetwork(STATE_SIZE, N_ACTIONS).to(device)
    target_net = QNetwork(STATE_SIZE, N_ACTIONS).to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    replay = ReplayBuffer(BUFFER_CAPACITY)

    cmd_name = "sumo-gui" if gui else "sumo"
    sumo_cmd = [cmd_name, "-c", sumo_cfg]

    traci.start(sumo_cmd)
    active_tls = list(traci.trafficlight.getIDList())
    primary_tls = active_tls[0] if active_tls else "C"
    print(f"SUMO started for RL. Controlling TLS list: {active_tls}")

    for _ in range(5):
        traci.simulationStep()

    counts = read_lane_counts(primary_tls)
    state = state_from_counts(counts)

    if train:
        print("Populating replay buffer with random interactions...")
        steps = 0
        while len(replay) < MIN_REPLAY_SIZE:
            a = random.randrange(N_ACTIONS)
            direction, g = apply_action(a, primary_tls)
            reward = accumulate_reward_during_green(g, active_tls)
            next_counts = read_lane_counts(primary_tls)
            next_state = state_from_counts(next_counts)
            done = False
            replay.push(state, a, reward, next_state, done)
            state = next_state
            steps += 1

        print("Starting training loop...")
        steps_done = 0
        while steps_done < n_steps:
            counts = read_lane_counts(primary_tls)
            state = state_from_counts(counts)

            action_idx = select_action(state, policy_net, steps_done)
            direction, green = apply_action(action_idx, primary_tls)

            reward = accumulate_reward_during_green(green, active_tls)
            next_counts = read_lane_counts(primary_tls)
            next_state = state_from_counts(next_counts)
            done = False

            replay.push(state, action_idx, reward, next_state, done)
            optimize_model(policy_net, target_net, optimizer, replay)

            if steps_done % TARGET_UPDATE == 0:
                target_net.load_state_dict(policy_net.state_dict())

            steps_done += 1

            if steps_done % 100 == 0:
                print(f"[step {steps_done}] reward={reward:.1f}, counts={next_counts}")

            if steps_done % 500 == 0:
                torch.save(policy_net.state_dict(), MODEL_SAVE_PATH)
                print("Model checkpoint saved.")

        torch.save(policy_net.state_dict(), MODEL_SAVE_PATH)
        print("Training finished. Model saved to", MODEL_SAVE_PATH)
    else:
        print("Running decentralized evaluation across all junctions...")
        if os.path.exists(MODEL_SAVE_PATH):
            policy_net.load_state_dict(torch.load(MODEL_SAVE_PATH, map_location="cpu"))
            policy_net.eval()
            print("Loaded trained model from", MODEL_SAVE_PATH)

        for step in range(500):
            traci.simulationStep()
            sim_time = traci.simulation.getTime()
            for tls in active_tls:
                c = read_lane_counts(tls)
                s = state_from_counts(c)
                with torch.no_grad():
                    qvals = policy_net(torch.tensor(s, dtype=torch.float32).unsqueeze(0)).numpy()[0]
                    a_idx = int(np.argmax(qvals))
                d, g = apply_action(a_idx, tls)
                if step % 50 == 0:
                    print(f"[t={sim_time:5.1f}] [{tls}] choose {d} for {g}s | counts={c}")

    traci.close()

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true", help="Train DQN online against SUMO")
    parser.add_argument("--steps", type=int, default=2000, help="Number of steps")
    parser.add_argument("--cfg", type=str, default="multi_junction.sumocfg", help="SUMO config file")
    parser.add_argument("--gui", action="store_true", help="Run with SUMO GUI")
    args = parser.parse_args()

    train_or_run(train=args.train, n_steps=args.steps, sumo_cfg=args.cfg, gui=args.gui)
