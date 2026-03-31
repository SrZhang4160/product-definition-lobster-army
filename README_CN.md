# 🦞 龙虾军团 — 多智能体产品分析系统

> **一个 Idea 进，一份工业级多维分析报告出。**
>
> 5 只 AI 龙虾 × CrewAI Flow 编排 × Anthropic Claude 驱动

```
版本：v2.0-worldclass
架构：CrewAI Flow + 5 Agents
技术栈：Anthropic Claude · CrewAI Flow · DSPy（阶段四）
```

---

## 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [五只龙虾](#五只龙虾)
4. [信息流设计](#信息流设计)
5. [核心机制](#核心机制)
6. [项目结构](#项目结构)
7. [快速开始](#快速开始)
8. [配置说明](#配置说明)
9. [成本估算](#成本估算)
10. [演进路线](#演进路线)

---

## 系统概述

龙虾军团是一个多智能体协作系统，接收一个原始产品 Idea，通过 5 只专业分工的 AI 龙虾协同工作，输出一份包含市场分析、竞争格局、产品定义、技术方案和风险评估的完整分析报告。

### 核心设计理念

- **锚点驱动**：从用户 Idea 中提取结构化锚点（名称 / 目标用户 / 场景 / 核心问题 / 一句话定位），贯穿全流程，确保所有分析不偏离主题
- **信息逐级压缩**：上游龙虾的全文输出经过 Haiku 压缩 + Schema 校验后传递给下游，在控制 token 成本的同时保持关键信息不丢失
- **语义一致性校验**：枢纽龙虾（L3）的输出会通过检查点 B 校验其与原始 Idea 的语义一致性，未通过则自动重跑
- **硬件级验收标准**：每只龙虾都有明确的 Gate Criteria（验收红线）和禁止行为清单，按世界一流团队标准设计

---

## 架构设计

```
用户 Idea
    │
    ▼
┌─────────────────┐
│  Phase 0: 锚点  │  Haiku 提取结构化锚点
│  generate_anchor │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ L1 市场 │ │ L2 竞品 │  ← Phase 1: 并行执行
│ Sonnet │ │ Sonnet │
└───┬────┘ └───┬────┘
    ▼          ▼
┌────────┐ ┌────────┐
│压缩 L1 │ │压缩 L2 │  ← Phase 2a/2b: Haiku 压缩
│ Haiku  │ │ Haiku  │
└───┬────┘ └───┬────┘
    └────┬─────┘
         ▼
    ┌─────────┐
    │合并摘要  │  ← Phase 2c: 合并 + Schema 校验
    └────┬────┘
         ▼
    ┌─────────┐
    │ L3 产品  │  ← Phase 3: 枢纽龙虾
    │ Sonnet  │
    └────┬────┘
         ▼
    ┌──────────┐
    │检查点 B   │  ← 语义一致性 ≥ 5/10?
    │ Haiku    │
    └──┬───┬───┘
  通过 │   │ 未通过
       ▼   ▼
    ┌────┐ ┌──────┐
    │    │ │重跑L3 │ → 再次检查 → 通过/中止
    │    │ └──────┘
    ▼
┌─────────┐
│ L4 技术  │  ← Phase 4: 读取 L3 全文
│ Sonnet  │
└────┬────┘
     ▼
┌─────────┐
│ L5 风控  │  ← Phase 5: 读取 L3+L4 全文
│ Sonnet  │
└────┬────┘
     ▼
┌─────────┐
│拼接报告  │  ← Phase 6: final_report.md + meta.json
└─────────┘
```

### 技术栈

| 组件 | 技术选型 | 用途 |
|------|---------|------|
| LLM 主力 | Claude Sonnet 4.6 | 5 只龙虾的推理引擎 |
| LLM 辅助 | Claude Haiku 4.5 | 锚点提取、压缩、校验 |
| 编排框架 | CrewAI Flow API | @start/@listen/@router 事件驱动 |
| 状态管理 | Pydantic BaseModel | 可序列化的 RunState |
| 数据校验 | JSON Schema | 压缩输出的结构校验 |

---

## 五只龙虾

### L1 · 首席市场情报官 (CMIO)
> 麦肯锡合伙人级行业分析 × Gartner 首席分析师级数据定量 × IDEO 人种志研究员级用户洞察

**核心交付物：**
- TAM/SAM/SOM 双方法交叉验证（Top-down + Bottom-up）
- 中国市场独立分析章节
- 10 维度用户画像（2-3 个 Persona）+ 首选用户群标注
- 市场窗口期判断（Too Early / Just Right / Late）
- 数据置信度三级标注（✅已验证 / ⚠️推算 / ❌未验证）

**验收红线：** TAM 双方法差异 > 30% 必须解释 · SOM 需引用可类比公司 benchmark · 禁止无来源数据

---

### L2 · 首席竞争情报官 (CCIO)
> CB Insights 首席分析师级竞品追踪 × 贝恩战略咨询级五力分析 × G2 用户声音挖掘

**核心交付物：**
- 替代方案全景图（正式工具 / 半正式方案 / 手动方案 / 关联替代品）
- 5-8 个竞品 × 12 维度深度矩阵
- 竞争力雷达图 + 战略群组地图 + 价值链弱点分析
- 3 个差异化切入方向（可行性 / 防御性 / 市场规模评分）
- CAC Benchmark（≥ 2 个同赛道数据点）

**验收红线：** ≥ 5 竞品且覆盖 ≥ 9/12 维度 · 融资/定价数据搜索验证 · 必须推荐最优切入点

---

### L3 · 首席产品官 (CPO) — 枢纽龙虾 🔑
> Superhuman 级产品定义 × IDEO 设计策略师级体验设计 × YC 合伙人级产品直觉

**核心交付物：**
- 产品定位三层金字塔 + ≤30 字一句话定位 + 差异化定位声明
- 五阶段用户旅程图（7 要素/阶段）+ Aha Moment 量化定义
- RICE + MoSCoW 混合功能优先级矩阵（每项有数据依据列）
- MVP 功能规格（用户故事 + 验收标准 + 边界条件）
- North Star Metric + 支撑指标 + 护栏指标
- MVP → V1 → V2 演进路径 + Go/No-Go 节点

**验收红线：** 定位忠实于锚点（否则触发回滚）· ≥ 5 处引用上游数据 · MVP ≤ 5 核心功能 · 必须有 Won't-have 列表

---

### L4 · 首席技术官 + 首席架构师 (CTO/CA)
> Stripe 级技术架构 × AWS SA Professional 级基础设施 × YC Technical Due Diligence 级评审

**核心交付物：**
- Top 5 架构决策记录（ADR）— 每个标注所支撑的 L3 功能
- 方案 A 精益 MVP：1-2 人 / 4-8 周 / 月运维 < $200
- 方案 B 增长版：3-5 人 / 支撑 10x / 月运维 < $2K
- 方案 C 平台版：企业级 / 100x / 含 AI + 多租户 + 合规
- 三方案对比矩阵（≥ 6 维度）+ Go/No-Go 演进路径
- Top 5 技术风险预警

**验收红线：** 技术栈精确到框架+版本 · 成本具体到月度金额范围 · 不允许过度架构 · 必须标注技术债务

---

### L5 · 首席风控官 + 红队队长 (CRO/RTL) — 最终守门人
> Sequoia 合伙人级投资审查 × 桥水风险分析师级系统思维 × 军事红队指挥官级对抗性思维

**核心交付物：**
- Pre-Mortem 致命假设检验（5-7 个隐含假设 + 验证方法 + Plan B）
- 六维系统性风险矩阵（市场 / 竞争 / 技术 / 团队 / 资金 / 合规）
- 三级资金链断裂压力测试（温和 / 严重 / 黑天鹅）
- 投资人尖锐问答（≥ 8 题 + 建议回答框架）
- 健康度评分卡（6 维度）+ Kill / Pivot / Go 明确决策

**验收红线：** 每个风险必须配缓解方案 · 缓解方案必须具体可执行 · 综合评分 3-8 区间 · 禁止纯粹恐吓

---

## 信息流设计

### 冷热存储分离

| 数据类型 | 存储方式 | 消费者 |
|---------|---------|--------|
| 锚点（Anchor） | 热存储 · 注入每只龙虾 | 全部 L1-L5 |
| L1/L2 全文 | 冷存储 · 压缩后传递 | L3（读摘要） |
| L1/L2 摘要 | 热存储 · JSON Schema 校验 | L3 |
| 合并摘要 | 热存储 · 存入 RunState | L3, L4, L5 |
| L3 全文 | 冷存储 · 直传 | L4, L5 |
| L4 全文 | 冷存储 · 直传 | L5 |

### 压缩三层防御

```
L1/L2 全文输出
    ↓
[Layer 1] Haiku LLM 压缩 → JSON 提取
    ↓ 失败？
[Layer 2] Schema 校验 → 重试一次
    ↓ 再失败？
[Layer 3] 规则引擎降级（正则提取 TAM/SAM/SOM）
```

---

## 核心机制

### 检查点 B — 语义一致性校验
L3（枢纽龙虾）的产品定义输出通过 Haiku 对原始 Idea 做语义一致性评分（0-10）：
- **≥ 5 分**：通过，继续执行 L4
- **< 5 分且首次**：升温重跑 L3（temperature 0.3 → 0.5）
- **< 5 分且已重试**：中止，生成部分报告

### 断点续跑
RunState 基于 Pydantic BaseModel，支持 JSON 序列化。每个 Phase 完成后自动 `persist()` 到 `runs/{run_id}/state.json`，支持通过 `--resume` 恢复。

### 锚点注入
从用户 Idea 中由 Haiku 提取的结构化锚点（name / target_user / scenario / core_problem / product_anchor）会注入到每只龙虾的 Prompt 开头，确保所有分析围绕同一产品定位展开。

---

## 项目结构

```
lobster-army/
├── .env                          # API Key
├── main.py                       # 入口脚本
├── flow.py                       # CrewAI Flow 核心编排
├── agents.py                     # 5 只龙虾 Agent 定义
├── state.py                      # RunState 状态模型
├── compression.py                # Haiku 压缩 + Schema 校验
├── gate_check.py                 # 检查点 B 语义一致性
├── config.yaml                   # 全局配置 + 验收权重
├── requirements.txt              # Python 依赖
├── README.md                     # English Blueprint
├── README_CN.md                  # 中文蓝图（本文件）
├── schemas/
│   ├── anchor.json               # 锚点 Schema
│   ├── summary_l1.json           # L1 摘要 Schema
│   ├── summary_l2.json           # L2 摘要 Schema
│   └── combined_summary.json     # 合并摘要 Schema
├── prompts/
│   ├── anchor/
│   │   ├── system.txt            # 锚点提取 Prompt（中文）
│   │   └── system_en.txt         # Anchor Extraction Prompt (English)
│   ├── lobster_1/
│   │   ├── system.txt            # L1 System Prompt（中文）
│   │   └── system_en.txt         # L1 System Prompt (English)
│   ├── lobster_2/ ... lobster_5/ # 同上双语结构
├── runs/                         # 运行输出目录
├── evals/results/                # 评估结果
└── tools/                        # 自定义工具
```

---

## 快速开始

### 1. 安装依赖
```bash
cd lobster-army
pip install -r requirements.txt
```

### 2. 配置 API Key
```bash
# .env 文件已包含，或手动设置：
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. 运行分析
```bash
# 新运行
python main.py "一个帮助远程团队异步协作的工具"

# 查看历史
python main.py --list

# 断点续跑
python main.py --resume 20260331_143022
```

### 4. 查看输出
```
runs/{run_id}/
├── final_report.md        # 完整分析报告
├── meta.json              # 运行元数据（成本/时间/评分）
├── state.json             # 可恢复的完整状态
└── combined_summary.json  # L1+L2 合并摘要
```

---

## 配置说明

`config.yaml` 中的关键配置项：

| 配置路径 | 说明 | 默认值 |
|---------|------|-------|
| `models.sonnet.name` | 主力模型 | claude-sonnet-4-6 |
| `models.haiku.name` | 辅助模型 | claude-haiku-4-5 |
| `lobsters.lobster_X.max_tokens` | 各龙虾最大输出 | 4000-5500 |
| `lobsters.lobster_X.temperature` | 各龙虾温度 | 0.3 (L5=0.4) |
| `lobsters.lobster_X.search_calls` | 搜索次数上限 | 0-6 |
| `gate_check.threshold` | 检查点 B 阈值 | 5 |
| `compression.max_tokens` | 压缩摘要长度 | 500 |
| `output.language` | 输出语言 | zh (中文) / en |

---

## 成本估算

| 组件 | 模型 | Input Tokens | Output Tokens | 成本/次 |
|------|------|-------------|--------------|---------|
| 锚点生成 | Haiku | ~200 | ~150 | $0.0010 |
| L1 市场分析 | Sonnet | ~7,300 | ~4,000 | $0.0819 |
| L2 竞品分析 | Sonnet | ~8,300 | ~4,000 | $0.0849 |
| 压缩 ×2 | Haiku | ~8,000 | ~1,000 | $0.0130 |
| L3 产品定义 | Sonnet | ~4,800 | ~3,500 | $0.0669 |
| 检查点 B | Haiku | ~1,000 | ~100 | $0.0015 |
| L4 技术方案 | Sonnet | ~8,800 | ~5,000 | $0.1014 |
| L5 风险分析 | Sonnet | ~14,800 | ~4,000 | $0.1044 |
| **单次运行总计** | | | | **~$0.48** |

启用 Prompt Caching 后可降至约 $0.40/次。

---

## 演进路线

| 阶段 | 目标 | 状态 |
|------|------|------|
| S1 | 代码脚手架 + 核心编排 | ✅ 已完成 |
| S2 | v2.0 世界一流 Prompt + 验收标准 | ✅ 已完成 |
| S3 | 双语支持（中/英） | ✅ 已完成 |
| S4 | 首次实战运行 + 输出质量评估 | ⏳ 下一步 |
| S5 | Few-shot 示例库 | 🔲 计划中 |
| S6 | 自动化评估脚本（eval pipeline） | 🔲 计划中 |
| S7 | DSPy Prompt 自动优化 | 🔲 计划中 |
| S8 | CrewAI AMP 云端部署 | 🔲 计划中 |
| S9 | Web UI + 实时进度展示 | 🔲 计划中 |
| S10 | 多语言报告输出 | 🔲 计划中 |

---

## 许可证

MIT License

---

*Built with 🦞 by 呆瓜军团*
