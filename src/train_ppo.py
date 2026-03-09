import gymnasium as gym
import numpy as np
import os
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt

# Fix for OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized.
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Ensure root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.monitor import Monitor

from src.env.poker_env import PokerEnv
from src.env.single_agent_wrapper import SingleAgentWrapper

def mask_fn(env: gym.Env) -> np.ndarray:
    return env.action_masks()

def plot_training_curves(log_dir: str, out_dir: str):
    monitor_file = os.path.join(log_dir, "monitor.csv")
    if not os.path.exists(monitor_file):
        return
    df = pd.read_csv(monitor_file, comment='#')
    if df.empty:
        return
    ep = np.arange(1, len(df) + 1)
    rewards = df["r"].to_numpy()
    lengths = df["l"].to_numpy()
    window = max(1, min(50, len(df)//10 if len(df) > 100 else 10))
    rewards_ma = pd.Series(rewards).rolling(window=window, min_periods=1).mean().to_numpy()
    lengths_ma = pd.Series(lengths).rolling(window=window, min_periods=1).mean().to_numpy()
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(ep, rewards, alpha=0.4, label="reward")
    plt.plot(ep, rewards_ma, color="C1", label=f"reward_ma({window})")
    plt.xlabel("episode")
    plt.ylabel("reward")
    plt.legend()
    plt.subplot(2, 1, 2)
    plt.plot(ep, lengths, alpha=0.4, label="length")
    plt.plot(ep, lengths_ma, color="C1", label=f"length_ma({window})")
    plt.xlabel("episode")
    plt.ylabel("length")
    plt.legend()
    os.makedirs(out_dir, exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "training_curves.png"))
    plt.close()

def save_eval_image(win_rate: float, avg_reward: float, out_dir: str, n_episodes: int):
    plt.figure(figsize=(8, 5))
    bars = plt.bar(["win_rate"], [win_rate * 100.0], color="C0")
    plt.ylim(0, 100)
    for b in bars:
        h = b.get_height()
        plt.text(b.get_x() + b.get_width() / 2, h + 1, f"{h:.1f}%", ha="center")
    plt.title("evaluation")
    txt = f"episodes: {n_episodes}\navg_reward: {avg_reward:.2f}"
    plt.gcf().text(0.75, 0.6, txt, fontsize=11, bbox=dict(facecolor="white", alpha=0.7, edgecolor="gray"))
    os.makedirs(out_dir, exist_ok=True)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "evaluation_summary.png"))
    plt.close()

def train():
    run_dir = os.path.join("logs", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(run_dir, exist_ok=True)
    env = PokerEnv()
    env = SingleAgentWrapper(env) # Opponents are RandomAgents

    # 2. Add Mask Wrapper
    env = ActionMasker(env, mask_fn)
    env = Monitor(env, run_dir) # Optional, for logging

    # 3. Create Model
    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=run_dir,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01
    )

    # 4. Train
    total_timesteps = 100000
    print(f"Training for {total_timesteps} timesteps...")

    model.learn(total_timesteps=total_timesteps, progress_bar=True)

    # 5. Save Final Model
    model.save("models/ppo_poker_final")
    print("Training finished. Model saved.")

    # 6. Evaluate
    plot_training_curves(run_dir, run_dir)
    win_rate, avg_reward = evaluate(model, env)
    save_eval_image(win_rate, avg_reward, run_dir, 100)

def evaluate(model, env, n_episodes=100):
    print(f"Evaluating model for {n_episodes} episodes...")
    wins = 0
    total_reward = 0

    # Note: env passed here is Wrapped(ActionMasker(SingleAgentWrapper(PokerEnv)))

    for i in range(n_episodes):
        obs, info = env.reset()
        terminated = False
        truncated = False
        episode_reward = 0

        while not (terminated or truncated):
            # 获取 mask from wrapped env
            # env is Monitor(ActionMasker(...))
            # ActionMasker exposes action_masks() via wrapper logic?
            # get_action_masks helper handles vectorized envs.
            # Here env is single env.
            # We can call action_masks directly on the env if it exposes it.
            # But ActionMasker puts it in info? No.
            # ActionMasker adds `action_masks` method to env.

            # For single env, use this helper:
            action_masks = get_action_masks(env)

            # Predict
            action, _states = model.predict(obs, action_masks=action_masks, deterministic=True)

            # Convert action to int if it's numpy array
            if isinstance(action, np.ndarray):
                action = action.item()

            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward

        total_reward += episode_reward

        # Check win
        # Need to unwrap to get game
        game = env.unwrapped.game
        # Hero ID is in wrapper
        # env.unwrapped is PokerEnv
        # We need SingleAgentWrapper instance to get hero_id
        # Iterate wrappers to find it
        hero_id = 0 # We know it's 0

        if game.winner == hero_id:
            wins += 1

    print(f"Win Rate: {wins / n_episodes * 100:.2f}%")
    print(f"Average Reward: {total_reward / n_episodes:.2f}")
    return wins / n_episodes, total_reward / n_episodes

if __name__ == "__main__":
    # Create logs/models dir
    os.makedirs("logs", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    train()
