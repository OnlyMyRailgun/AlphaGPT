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

## 🚀 快速开始

### 1. 环境准备

建议使用 **Docker Compose**（包含自动安装 PostgreSQL 数据库）。

1.  **复制配置模板**:
    ```bash
    cp .env.example .env
    ```
    编辑 `.env` 文件，填入你的 **BIRDEYE_API_KEY** 及 **SOLANA_PRIVATE_KEY**。

2.  **启动容器**:
    ```bash
    docker-compose up -d
    ```

### 2. 运行主流程

你也可以直接在宿主机（需 Python 3.10+）运行，但需确保数据库已准备完毕。

#### Step 2.1: 抓取链上数据 (Data Pipeline)
从数据源同步 Token 信息及 OHLCV 行情：
```bash
docker-compose run app python -m data_pipeline.run_pipeline
```

#### Step 2.2: 策略/因子挖掘 (Alpha Mining)
启动 Transformer 训练，生成最优选币公式 (`best_meme_strategy.json`):
```bash
docker-compose run app python -m model_core.engine
```

#### Step 2.3: 启动监控面板 (Dashboard)
看板会随 `docker-compose up` 默认启动，在浏览器访问:
👉 [http://localhost:8501](http://localhost:8501)

#### Step 2.4: 实盘策略执行 (Live Trader)
加载挖掘出的公式，开始实时扫描市场并自动下单（风险提示：务必从小额开始）：
```bash
docker-compose run app python -m strategy_manager.runner
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
