import gymnasium as gym
import numpy as np
import os
import sys

# Ensure root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor

from src.env.poker_env import PokerEnv
from src.env.single_agent_wrapper import SingleAgentWrapper

def mask_fn(env: gym.Env) -> np.ndarray:
    return env.action_masks()

def train():
    # 1. Create Env
    env = PokerEnv()
    env = SingleAgentWrapper(env) # Opponents are RandomAgents
    
    # 2. Add Mask Wrapper
    env = ActionMasker(env, mask_fn)
    env = Monitor(env) # Optional, for logging
    
    # 3. Create Model
    model = MaskablePPO(
        "MlpPolicy", 
        env, 
        verbose=1,
        tensorboard_log="./logs/",
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
    
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path="./models/",
        name_prefix="ppo_poker"
    )
    
    model.learn(total_timesteps=total_timesteps, callback=checkpoint_callback)
    
    # 5. Save Final Model
    model.save("models/ppo_poker_final")
    print("Training finished. Model saved.")
    
    # 6. Evaluate
    evaluate(model, env)

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

if __name__ == "__main__":
    # Create logs/models dir
    os.makedirs("logs", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    train()
