from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from sumo_env import TrafficEnv


# ==============================
# CHANGE THIS TO YOUR FILE PATH
# ==============================
SUMO_CFG_PATH = "sumo/4way.sumocfg"


def main():
    # Create SUMO-based environment
    env = TrafficEnv(SUMO_CFG_PATH)

    # Wrap with Monitor (required by SB3)
    env = Monitor(env)

    # PPO Model
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=256,
        gamma=0.99,
        verbose=1
    )

    # Train
    model.learn(total_timesteps=10_000)

    # Save model
    model.save("ppo_sumo_traffic")

    # Close environment
    env.close()


if __name__ == "__main__":
    main()
