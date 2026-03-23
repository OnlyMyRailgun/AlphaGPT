# AlphaGPT: 因子生成式 Solana 量化交易系统

AlphaGPT 是一套集“深度因子挖掘”与“实盘自动执行”于一体的 Solana Memecoin 量化交易系统。

其核心逻辑并非直接预测价格，而是利用 **Transformer 模型自动生成可解释的因子公式 (Token 序列)**，通过在高频链上数据上的回测表现进行强化学习，最终筛选出高分公式用于实时扫描与自动下单。

---

## 🌟 核心特性

- **因子生成器 (Factor GPT)**: 基于 Transformer 的算子序列生成，支持复杂公式组合。
- **LoRD 正则化**: 采用 Low-Rank Decay 优化注意力矩阵，提升因子的泛化能力。
- **硬件加速支持**: 已适配 **Apple Silicon (MPS)** 与 NVIDIA CUDA，支持 MacBook M1/M2/M3 硬件加速。
- **全栈容器化**: 提供 Docker Compose 一键式部署 PostgreSQL 数据库及运行环境。
- **实时看板**: 集成 Streamlit 可视化控制台，实时查看持仓、PnL 与系统日志。

---

### 1. 环境准备

推荐使用 **Docker Compose** 启动数据库，使用 **uv** 在本地运行代码（以获得 Apple Silicon GPU 加速）。

1.  **准备环境与数据库**:
    ```bash
    # 启动数据库容器
    docker-compose up -d db

    # 复制环境配置
    cp .env.example .env
    ```
    编辑 `.env` 文件，确保 `DB_HOST=localhost`。

2.  **本地运行训练**:
    ```bash
    # 使用 uv 直接运行（它会自动管理 Python 版本和依赖）
    uv run python -m model_core.engine
    ```

---

## 🚀 运行流程 (推荐搭配 uv)

#### Step 2.1: 抓取数据 (Data Pipeline)
```bash
uv run python -m data_pipeline.run_pipeline
```

#### Step 2.2: 策略因子挖掘 (Alpha Mining)
这步会调用 Mac 的 MPS 加速，速度比 Docker 快百倍：
```bash
uv run python -m model_core.engine
```

#### Step 2.3: 启动可视化看板 (Dashboard)
```bash
uv run streamlit run dashboard/app.py
```

---

## 📁 目录结构

```text
├── data_pipeline/      # 数据抓取与 TimescaleDB 存储
├── model_core/         # 因子生成模型 (Transformer)、VM 解释器、回测引擎
├── strategy_manager/   # 实盘风控、持仓管理逻辑
├── execution/          # Solana RPC 封装、Jupiter 聚合器集成
├── dashboard/          # Streamlit 可视化看板
└── docker-compose.yml  # 容器化环境配置
```

---

## 🛠️ 高级配置 (MacBook 加速)

项目已通过 `ModelConfig.DEVICE` 自动适配 Mac 硬件：
- **Apple Silicon (M1/M2/M3)**: 自动使用 `mps` (Metal) 模式，单卡训练效率极高。
- **Linux/NVIDIA**: 自动使用 `cuda` 后端。

---

## ⚠️ 免责声明

本仓库提供的代码仅供研究与参考，**不构成任何投资建议**。
加密货币市场（特别是 Meme Coin 生态）具有极高波动风险，在进行 Live Trading 之前请务必充分理解代码逻辑并承担相应财务责任。
目前双方已达成和解。
