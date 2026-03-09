import gymnasium as gym
import numpy as np
import random
from typing import List, Optional, Tuple, Dict, Any
from src.agent.random_agent import RandomAgent
from src.agent.heuristic_agent import HeuristicAgent

class SingleAgentWrapper(gym.Wrapper):
    """
    将 3人 PokerEnv 包装为单人训练环境。
    - 训练 Agent 固定为 Player 0。
    - 其他 2 个位置由 opponent_agents 控制。
    - 支持混合对手：RandomAgent 和 HeuristicAgent。
    """
    
    def __init__(self, env: gym.Env, opponents: List = None, mixed_opponents: bool = True):
        super().__init__(env)
        
        # 训练对象固定为 Player 0
        self.hero_id = 0
        self.mixed_opponents = mixed_opponents
        
        # 初始化对手库
        self.random_opponents = [
            RandomAgent(env.action_space.n), 
            RandomAgent(env.action_space.n)
        ]
        self.heuristic_opponents = [
            HeuristicAgent(),
            HeuristicAgent()
        ]
        
        # 当前对局使用的对手
        if opponents is not None:
            self.opponents = opponents
        else:
            self.opponents = self.random_opponents
            
        self.last_action_mask = None
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        # 如果开启了混合对手，每次重置时有概率切换对手
        if self.mixed_opponents:
            # 50% 概率使用启发式对手，50% 随机
            if random.random() < 0.5:
                self.opponents = self.heuristic_opponents
            else:
                self.opponents = self.random_opponents

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
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        total_reward = reward
        
        if terminated or truncated:
            self.last_action_mask = info.get("action_mask")
            return obs, total_reward, terminated, truncated, info
            
        # 2. 轮到对手，自动推进
        obs, opp_reward, terminated, truncated, info = self._play_until_hero(obs, info)
        
        # 3. 控牌奖励判定 (夺回出牌权)
        # 如果推进后，又回到了 Hero 的自由出牌轮 (last_play 为 None)，说明 Hero 刚才的出牌没人管得住
        if not terminated and not truncated:
            game = self.env.unwrapped.game
            if game.current_player == self.hero_id and game.last_play is None:
                total_reward += 5.0  # 夺回出牌权奖励
        
        # 4. 终局奖励重塑
        if terminated:
            game = self.env.unwrapped.game
            winner = game.winner
            if winner == self.hero_id:
                # 胜利奖励保持 +100 (已经在 env.step 中处理了一部分，这里可以追加或修正)
                # 目前 env.step 在 is_over 时给执行者 +100
                pass
            else:
                # 输了：降低固定惩罚，增加减损奖励
                # 原逻辑: -100 - remain
                # 新逻辑: -50 - (remain * 2)  # 剩的越多罚得越狠，剩 1 张罚 52，剩 15 张罚 80
                remain = len(game.hands[self.hero_id])
                total_reward -= 50.0
                total_reward -= (remain * 2.0)
        
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
