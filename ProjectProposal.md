# 跑得快 (Run Fast) AI & API 项目策划方案

## 1. 项目概述
本项目旨在开发一个基于深度学习的"跑得快"（3人版，45张牌）游戏服务端。核心目标是训练一个能像人类一样思考的AI模型，并通过API接口对外提供对战服务，允许人类玩家接入挑战。

## 2. 可行性分析 (Feasibility Analysis)

### 2.1 技术可行性 (High)
*   **游戏逻辑**：跑得快规则相对固定，状态空间虽然大（牌型组合多），但远小于围棋，适合强化学习（Reinforcement Learning, RL）。
*   **AI模型**：使用 **Deep Q-Network (DQN)** 或 **PPO (Proximal Policy Optimization)** 是目前业界处理此类不完全信息博弈（Imperfect Information Game）的标准解法。
*   **开发语言**：Python 是最佳选择，它既是 AI 领域的通用语言（PyTorch/TensorFlow），也是优秀的后端语言（FastAPI/Django）。

### 2.2 难点与挑战 (Challenges)
1.  **牌型编码 (State Representation)**：如何把手中的牌、桌上的牌、历史出牌记录转换成神经网络能理解的 "0101" 矩阵。
2.  **合法动作生成 (Legal Action Generation)**：跑得快有"必压"规则（能管必须管），这要求游戏引擎必须能极其准确地计算出当前所有合法的出牌组合。
3.  **模型训练时间**：深度强化学习需要大量的自我对弈（Self-Play）来积累经验，训练初期AI会非常笨，需要耐心和算力。

### 2.3 结论
**完全可行**。作为一个学习型项目，它能涵盖 **游戏逻辑算法**、**深度学习**、**后端API开发** 三大核心领域，非常适合进阶。

---

## 3. 技术架构 (Technical Architecture)

我们将项目分为三个核心模块：

```mermaid
graph TD
    User[玩家/前端] -->|HTTP/WebSocket| API[API 服务层 (FastAPI)]
    API -->|Action| GameEngine[游戏核心引擎 (Rules)]
    API -->|State| AI[AI 推理模型 (PyTorch)]
    AI -->|Decision| GameEngine
```

### 3.1 核心技术栈
*   **语言**: Python 3.9+
*   **Web框架**: FastAPI (高性能，适合异步IO)
*   **AI框架**: PyTorch (灵活性高，适合研究)
*   **数据处理**: NumPy (矩阵运算)
*   **训练环境**: Gym (OpenAI 标准强化学习接口)

---

## 4. 开发计划 (Development Roadmap)

### 第一阶段：游戏核心引擎 (The Foundation)
**目标**：实现一个只要给它指令，它就能按规则运行的"裁判"。
*   [ ] 定义牌的数据结构（Card, Hand）。
*   [ ] 实现牌型判断算法（单张、对子、顺子、炸弹等）。
*   [ ] **关键点**：实现 `get_legal_actions(state)` 函数，根据当前桌面牌型，计算出玩家所有合法的出牌选择（包含"过"）。
*   [ ] 实现游戏状态流转（发牌、出牌、结算、下一位）。

### 第二阶段：AI 环境搭建 (The Gym)
**目标**：让 AI 能"玩"这个游戏。
*   [ ] 封装 Gym Environment：实现 `reset()` (开始新游戏) 和 `step(action)` (执行动作并返回奖励)。
*   [ ] 定义 **State (状态)**：
    *   我的手牌（One-hot编码）
    *   其他两家剩余牌数
    *   当前桌面上最大的牌
    *   历史出牌记录
*   [ ] 定义 **Reward (奖励)**：
    *   赢了 +100
    *   输了 -剩余牌数
    *   打出炸弹 +20
    *   非法出牌 -1000 (强制结束)

### 第三阶段：AI 训练 (The Brain)
**目标**：从"随机乱打"进化到"策略高手"。
*   [ ] **基准测试 (Baseline)**：先写一个 `RandomAgent` (随机出牌) 和 `RuleAgent` (简单规则：有小打小，有大管上)。
*   [ ] **DQN/PPO 算法实现**：搭建神经网络（输入状态 -> 输出动作概率）。
*   [ ] **自我对弈 (Self-Play)**：让模型自己跟自己打，或者跟历史版本的自己打，不断进化。

### 第四阶段：API 服务化 (The Interface)
**目标**：让外部程序能调用这个AI。
*   [ ] 搭建 FastAPI 项目。
*   [ ] 接口设计：
    *   `POST /game/start`: 开始一局新游戏，返回 GameID。
    *   `POST /game/action`: 玩家出牌。
    *   `GET /game/state`: 获取当前局面。
*   [ ] 接入 AI 模型进行实时推理。

---

## 5. 下一步建议 (Next Steps)

鉴于您希望从基础做起，建议我们 **先完成第一阶段：游戏核心引擎**。
没有完善的规则引擎，AI 训练就无从谈起。

**是否立即开始编写第一阶段的“扑克牌定义”和“基础规则”代码？**
