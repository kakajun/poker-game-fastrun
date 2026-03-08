import gymnasium as gym
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from src.agent.random_agent import RandomAgent

class SingleAgentWrapper(gym.Wrapper):
    """
    将 3人 PokerEnv 包装为单人训练环境。
    - 训练 Agent 固定为 Player 0。
    - 其他 2 个位置由 opponent_agents 控制（默认为 RandomAgent）。
    - reset() 和 step() 会自动跳过对手回合，直到轮到 Hero (Player 0) 或游戏结束。
    """
    
    def __init__(self, env: gym.Env, opponents: List = None):
        super().__init__(env)
        
        # 训练对象固定为 Player 0
        self.hero_id = 0
        
        # 初始化对手 Agent (Player 1, Player 2)
        if opponents is None:
            # 默认两个 RandomAgent
            self.opponents = [
                RandomAgent(env.action_space.n), 
                RandomAgent(env.action_space.n)
            ]
        else:
            self.opponents = opponents
            
        assert len(self.opponents) == 2, "Must provide exactly 2 opponents for 3-player game"

        self.last_action_mask = None
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        # 重置环境
        obs, info = self.env.reset(seed=seed, options=options)
        
        # 如果当前玩家不是 Hero，自动推进
        current_player = info["player_id"]
        if current_player != self.hero_id:
            obs, _, terminated, truncated, info = self._play_until_hero(obs, info)
            
        self.last_action_mask = info.get("action_mask")
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        执行 Hero 的动作，然后自动推进对手回合。
        返回给 Hero 的是累计奖励和下一个 Hero 观测。
        """
        # 1. Hero 执行动作
        # 此时轮到 Hero，obs 是给 Hero 的
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        total_reward = reward
        
        if terminated or truncated:
            self.last_action_mask = info.get("action_mask")
            return obs, total_reward, terminated, truncated, info
            
        # 2. 轮到对手，自动推进
        # 此时 obs 是给下一个玩家（对手）的
        obs, opp_reward, terminated, truncated, info = self._play_until_hero(obs, info)
        
        # 3. 累计奖励
        if terminated:
            # 检查赢家
            winner = self.env.unwrapped.game.winner
            if winner != self.hero_id:
                # Hero 输了
                total_reward -= 100.0
                remain = len(self.env.unwrapped.game.hands[self.hero_id])
                total_reward -= remain
        
        self.last_action_mask = info.get("action_mask")
        return obs, total_reward, terminated, truncated, info
        
    def action_masks(self) -> np.ndarray:
        """
        Return action masks for MaskablePPO.
        Should return boolean array (True=valid, False=invalid).
        Our env returns 0/1 int8, need to convert.
        """
        if self.last_action_mask is None:
            # Should not happen if reset called
            return np.ones(self.env.action_space.n, dtype=bool)
        return self.last_action_mask.astype(bool)

    def _play_until_hero(self, obs, info):
        """
        循环让对手行动，直到轮到 Hero 或游戏结束。
        """
        terminated = False
        truncated = False
        reward = 0.0
        
        while not (terminated or truncated):
            current_player = info["player_id"]
            
            if current_player == self.hero_id:
                # 轮到 Hero 了，退出循环
                break
                
            # 轮到对手
            # Map player_id to opponent index
            # Player 1 -> index 0
            # Player 2 -> index 1
            opp_idx = current_player - 1
            if opp_idx < 0 or opp_idx >= 2:
                # Should not happen if hero_id=0
                raise ValueError(f"Invalid opponent index: {opp_idx} for player {current_player}")
                
            agent = self.opponents[opp_idx]
            mask = info["action_mask"]
            
            # Agent act
            action = agent.act(obs, mask)
            
            # Step
            obs, r, terminated, truncated, info = self.env.step(action)
            reward += r # 这里的 reward 是给对手的，Hero 不关心
            
        return obs, reward, terminated, truncated, info
