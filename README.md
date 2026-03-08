# Poker Game FastRun AI (跑得快 AI)

这是一个基于强化学习 (PPO) 的跑得快游戏 AI 项目。
包含核心游戏引擎、Gym 训练环境、PPO 训练管线、FastAPI 后端服务以及 Vue 3 前端界面。

## 🎯 项目成果

- **AI 胜率**: 64% (vs 随机策略)
- **训练环境**: OpenAI Gym + Maskable PPO (处理非法动作)
- **技术栈**: Python 3.9, PyTorch, Stable-Baselines3, FastAPI, Vue 3, TypeScript

## 📂 目录结构

```
poker-game-fastrun/
├── src/                # 后端源码
│   ├── core/           # 游戏核心逻辑 (规则、发牌、判胜)
│   ├── env/            # Gym 环境 (ActionSpace, Observation, Reward)
│   ├── agent/          # AI 代理 (RandomAgent, PPO Wrapper)
│   ├── api/            # FastAPI 服务接口
│   └── train_ppo.py    # PPO 训练脚本
├── front/              # 前端源码 (Vue 3 + Vite)
├── models/             # 训练好的模型文件
├── tests/              # 单元测试
└── environment.yml     # Conda 环境配置
```

## 🚀 快速开始

### 1. 环境准备

确保已安装 Conda。

```bash
# 创建并激活环境
conda env create -f environment.yml
conda activate poker-rl

# 如果需要手动安装核心依赖 (Windows)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install sb3-contrib stable-baselines3 shimmy fastapi uvicorn pydantic numpy
```

### 2. 启动后端服务

后端提供游戏逻辑和 AI 推理接口。

```bash
# 在项目根目录下运行
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，API 文档位于: `http://localhost:8000/docs`

### 3. 启动前端界面

前端提供可视化的游戏交互。

```bash
# 进入前端目录
cd front

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

浏览器访问: `http://localhost:5173` (或终端显示的端口)

### 4. 训练 AI (可选)

如果你想重新训练模型：

```bash
# 运行训练脚本 (使用 CPU 训练约需 5-10 分钟)
python src/train_ppo.py
```

模型将保存到 `models/ppo_poker_final.zip`。

## 🧠 核心逻辑

### 状态空间 (Observation)
- **手牌 (52维)**: One-hot 编码
- **剩余牌数 (2维)**: 对手手牌数量
- **上家出牌 (62维)**: 牌型、牌值、长度

### 动作空间 (Action)
- **252 维离散空间**: 包含 Pass 和所有可能的合法牌型抽象 (Type + Length + MaxRank)。
- **Masking**: 使用 Action Masking 技术屏蔽非法动作，加速训练收敛。

### 奖励函数 (Reward)
- **胜负**: +100 / -100
- **步数惩罚**: 每步 -1 (鼓励快速出完)
- **炸弹奖励**: +20
- **输家惩罚**: -剩余牌数

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 许可证

MIT License
