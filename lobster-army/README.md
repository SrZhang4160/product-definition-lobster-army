# 🦞 Lobster Army — Multi-Agent Product Analysis System

> **One Idea in, one industrial-grade multi-dimensional analysis report out.**
>
> 5 AI Lobsters × CrewAI Flow Orchestration × Anthropic Claude Powered

```
Version: v2.0-worldclass
Architecture: CrewAI Flow + 5 Agents
Tech Stack: Anthropic Claude · CrewAI Flow · DSPy (Phase 4)
```

**[中文版蓝图 →](README_CN.md)**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [The Five Lobsters](#the-five-lobsters)
4. [Information Flow](#information-flow)
5. [Core Mechanisms](#core-mechanisms)
6. [Project Structure](#project-structure)
7. [Quick Start](#quick-start)
8. [Configuration](#configuration)
9. [Cost Estimation](#cost-estimation)
10. [Roadmap](#roadmap)

---

## System Overview

Lobster Army is a multi-agent collaboration system that takes a raw product Idea as input, runs it through 5 specialized AI lobsters working in concert, and outputs a comprehensive analysis report covering market sizing, competitive landscape, product definition, technical implementation, and risk assessment.

### Core Design Principles

- **Anchor-Driven**: A structured anchor (name / target user / scenario / core problem / one-liner positioning) is extracted from the user's Idea and injected into every lobster's prompt, ensuring all analysis stays on-topic
- **Progressive Compression**: Upstream lobsters' full outputs are compressed via Haiku + Schema validation before passing downstream, controlling token costs while preserving critical information
- **Semantic Consistency Gate**: The pivot lobster's (L3) output goes through Gate Check B to verify semantic alignment with the original Idea — failures trigger automatic reruns
- **Hardware-Grade Acceptance Criteria**: Every lobster has explicit Gate Criteria (acceptance red lines) and prohibited behavior lists, designed to world-class team standards

---

## Architecture

```
User Idea
    │
    ▼
┌──────────────────┐
│  Phase 0: Anchor  │  Haiku extracts structured anchor
│  generate_anchor  │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│L1 Mkt  │ │L2 Comp │  ← Phase 1: Parallel execution
│ Sonnet │ │ Sonnet │
└───┬────┘ └───┬────┘
    ▼          ▼
┌────────┐ ┌────────┐
│Compress│ │Compress│  ← Phase 2a/2b: Haiku compression
│ Haiku  │ │ Haiku  │
└───┬────┘ └───┬────┘
    └────┬─────┘
         ▼
    ┌──────────┐
    │  Merge   │  ← Phase 2c: Merge + Schema validation
    └────┬─────┘
         ▼
    ┌──────────┐
    │L3 Product│  ← Phase 3: Pivot Lobster
    │  Sonnet  │
    └────┬─────┘
         ▼
    ┌──────────┐
    │ Gate B   │  ← Semantic consistency ≥ 5/10?
    │  Haiku   │
    └──┬───┬───┘
  Pass │   │ Fail
       ▼   ▼
    ┌────┐ ┌───────┐
    │    │ │Retry  │ → Re-check → Pass/Abort
    │    │ │  L3   │
    │    │ └───────┘
    ▼
┌──────────┐
│ L4 Tech  │  ← Phase 4: Reads L3 full text
│  Sonnet  │
└────┬─────┘
     ▼
┌──────────┐
│ L5 Risk  │  ← Phase 5: Reads L3+L4 full text
│  Sonnet  │
└────┬─────┘
     ▼
┌──────────┐
│ Assemble │  ← Phase 6: final_report.md + meta.json
└──────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Primary LLM | Claude Sonnet 4.6 | Reasoning engine for all 5 lobsters |
| Auxiliary LLM | Claude Haiku 4.5 | Anchor extraction, compression, gate checks |
| Orchestration | CrewAI Flow API | @start/@listen/@router event-driven pipeline |
| State Mgmt | Pydantic BaseModel | Serializable RunState with checkpoint/resume |
| Validation | JSON Schema | Structural validation of compressed outputs |

---

## The Five Lobsters

### L1 · Chief Market Intelligence Officer (CMIO)
> McKinsey Partner-level industry analysis × Gartner Chief Analyst-level quantitative rigor × IDEO Ethnographer-level user insight

**Core Deliverables:**
- TAM/SAM/SOM with dual-method cross-validation (Top-down + Bottom-up)
- Independent China market analysis chapter
- 10-dimension user personas (2-3 Personas) with Primary Persona designation
- Market timing judgment (Too Early / Just Right / Late)
- Three-tier data confidence labels (✅Verified / ⚠️Estimated / ❌Unverified)

**Acceptance Red Lines:** TAM dual-method gap > 30% requires explanation · SOM must reference comparable company benchmarks · No unsourced data allowed

---

### L2 · Chief Competitive Intelligence Officer (CCIO)
> CB Insights Chief Analyst-level competitor tracking × Bain strategic consulting-level Five Forces analysis × G2 user voice mining

**Core Deliverables:**
- Alternative solutions landscape (formal tools / semi-formal solutions / manual processes / adjacent substitutes)
- 5-8 competitors × 12-dimension deep matrix
- Competitive radar chart + Strategic group map + Value chain vulnerability analysis
- 3 differentiation entry strategies (feasibility / defensibility / market size scores)
- CAC Benchmark (≥ 2 data points from same vertical)

**Acceptance Red Lines:** ≥ 5 competitors covering ≥ 9/12 dimensions · Funding/pricing data must be search-verified · Must recommend optimal entry point

---

### L3 · Chief Product Officer (CPO) — Pivot Lobster 🔑
> Superhuman-level product definition × IDEO Design Strategist-level experience design × YC Partner-level product instinct

**Core Deliverables:**
- Three-layer product positioning pyramid + ≤30 char one-liner + differentiation statement
- Five-stage user journey map (7 elements/stage) + quantified Aha Moment definition
- RICE + MoSCoW hybrid feature priority matrix (with data evidence column)
- MVP feature specs (User Stories + Acceptance Criteria + boundary conditions)
- North Star Metric + supporting metrics + guardrail metrics
- MVP → V1 → V2 evolution path with Go/No-Go gates

**Acceptance Red Lines:** Positioning must align with anchor (deviation triggers rollback) · ≥ 5 upstream data citations · MVP ≤ 5 core features · Must include Won't-have list

---

### L4 · Chief Technology Officer + Chief Architect (CTO/CA)
> Stripe-level technical architecture × AWS SA Professional-level infrastructure × YC Technical Due Diligence-level review

**Core Deliverables:**
- Top 5 Architecture Decision Records (ADR) — each mapped to L3 features
- Plan A Lean MVP: 1-2 engineers / 4-8 weeks / monthly ops < $200
- Plan B Growth Edition: 3-5 team / 10x scalability / monthly ops < $2K
- Plan C Platform Edition: enterprise-grade / 100x / AI + multi-tenancy + compliance
- Three-plan comparison matrix (≥ 6 dimensions) + Go/No-Go evolution path
- Top 5 technical risk warnings

**Acceptance Red Lines:** Tech stack precise to framework + version · Costs specific to monthly ranges · No over-engineering · Must disclose tech debt

---

### L5 · Chief Risk Officer + Red Team Lead (CRO/RTL) — Final Gatekeeper
> Sequoia Partner-level investment review × Bridgewater Risk Analyst-level systems thinking × Military Red Team Commander-level adversarial mindset

**Core Deliverables:**
- Pre-Mortem fatal assumption audit (5-7 hidden assumptions + validation methods + Plan B)
- Six-dimensional systemic risk matrix (Market / Competition / Tech / Team / Capital / Compliance)
- Three-tier cash runway stress tests (Mild / Severe / Black Swan)
- Investor tough Q&A (≥ 8 questions + suggested answer frameworks)
- Health scorecard (6 dimensions) + explicit Kill / Pivot / Go decision

**Acceptance Red Lines:** Every risk must have a mitigation plan · Mitigations must be actionable · Score range 3-8 · No pure fear-mongering

---

## Information Flow

### Hot/Cold Storage Separation

| Data Type | Storage | Consumers |
|-----------|---------|-----------|
| Anchor | Hot · injected into every lobster | All L1-L5 |
| L1/L2 Full Text | Cold · compressed before passing | L3 (reads summary) |
| L1/L2 Summaries | Hot · JSON Schema validated | L3 |
| Combined Summary | Hot · stored in RunState | L3, L4, L5 |
| L3 Full Text | Cold · passed directly | L4, L5 |
| L4 Full Text | Cold · passed directly | L5 |

### Three-Layer Compression Defense

```
L1/L2 Full Output
    ↓
[Layer 1] Haiku LLM Compression → JSON Extraction
    ↓ Failed?
[Layer 2] Schema Validation → Retry once
    ↓ Failed again?
[Layer 3] Rule-based fallback (regex extract TAM/SAM/SOM)
```

---

## Core Mechanisms

### Gate Check B — Semantic Consistency Validation
L3's (Pivot Lobster) product definition output is scored by Haiku against the original Idea for semantic consistency (0-10):
- **≥ 5**: Pass, proceed to L4
- **< 5, first attempt**: Retry L3 with higher temperature (0.3 → 0.5)
- **< 5, already retried**: Abort, generate partial report

### Checkpoint Resume
RunState is a Pydantic BaseModel that serializes to JSON. After each Phase completion, it auto-persists to `runs/{run_id}/state.json`, enabling `--resume` recovery.

### Anchor Injection
A structured anchor (name / target_user / scenario / core_problem / product_anchor) extracted from the user's Idea by Haiku is injected at the beginning of every lobster's prompt, ensuring all analyses orbit the same product positioning.

---

## Project Structure

```
lobster-army/
├── .env                          # API Key
├── main.py                       # Entry point
├── flow.py                       # CrewAI Flow core orchestration
├── agents.py                     # 5 Lobster Agent definitions
├── state.py                      # RunState state model
├── compression.py                # Haiku compression + Schema validation
├── gate_check.py                 # Gate Check B semantic consistency
├── config.yaml                   # Global config + acceptance weights
├── requirements.txt              # Python dependencies
├── README.md                     # English Blueprint (this file)
├── README_CN.md                  # Chinese Blueprint
├── schemas/
│   ├── anchor.json               # Anchor Schema
│   ├── summary_l1.json           # L1 Summary Schema
│   ├── summary_l2.json           # L2 Summary Schema
│   └── combined_summary.json     # Combined Summary Schema
├── prompts/
│   ├── anchor/
│   │   ├── system.txt            # Anchor Prompt (Chinese)
│   │   └── system_en.txt         # Anchor Prompt (English)
│   ├── lobster_1/
│   │   ├── system.txt            # L1 System Prompt (Chinese)
│   │   └── system_en.txt         # L1 System Prompt (English)
│   ├── lobster_2/ ... lobster_5/ # Same bilingual structure
├── runs/                         # Run output directory
├── evals/results/                # Evaluation results
└── tools/                        # Custom tools
```

---

## Quick Start

### 1. Install Dependencies
```bash
cd lobster-army
pip install -r requirements.txt
```

### 2. Configure API Key
```bash
# .env file is included, or manually set:
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run Analysis
```bash
# New run (Chinese)
python main.py "一个帮助远程团队异步协作的工具"

# New run (English) — set language in config.yaml: output.language: en
python main.py "A tool that helps remote teams collaborate asynchronously"

# List history
python main.py --list

# Resume from checkpoint
python main.py --resume 20260331_143022
```

### 4. View Output
```
runs/{run_id}/
├── final_report.md        # Complete analysis report
├── meta.json              # Run metadata (cost/timing/scores)
├── state.json             # Resumable full state
└── combined_summary.json  # L1+L2 merged summary
```

---

## Configuration

Key fields in `config.yaml`:

| Config Path | Description | Default |
|-------------|------------|---------|
| `models.sonnet.name` | Primary model | claude-sonnet-4-6 |
| `models.haiku.name` | Auxiliary model | claude-haiku-4-5 |
| `lobsters.lobster_X.max_tokens` | Max output per lobster | 4000-5500 |
| `lobsters.lobster_X.temperature` | Temperature per lobster | 0.3 (L5=0.4) |
| `lobsters.lobster_X.search_calls` | Search call limit | 0-6 |
| `gate_check.threshold` | Gate B threshold | 5 |
| `compression.max_tokens` | Compressed summary length | 500 |
| `output.language` | Output language | zh / en |

---

## Cost Estimation

| Component | Model | Input Tokens | Output Tokens | Cost/Run |
|-----------|-------|-------------|--------------|----------|
| Anchor Gen | Haiku | ~200 | ~150 | $0.0010 |
| L1 Market | Sonnet | ~7,300 | ~4,000 | $0.0819 |
| L2 Competitive | Sonnet | ~8,300 | ~4,000 | $0.0849 |
| Compress ×2 | Haiku | ~8,000 | ~1,000 | $0.0130 |
| L3 Product | Sonnet | ~4,800 | ~3,500 | $0.0669 |
| Gate Check B | Haiku | ~1,000 | ~100 | $0.0015 |
| L4 Technical | Sonnet | ~8,800 | ~5,000 | $0.1014 |
| L5 Risk | Sonnet | ~14,800 | ~4,000 | $0.1044 |
| **Total per run** | | | | **~$0.48** |

With Prompt Caching enabled, costs reduce to approximately $0.40/run.

---

## Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| S1 | Code scaffold + core orchestration | ✅ Done |
| S2 | v2.0 world-class prompts + acceptance criteria | ✅ Done |
| S3 | Bilingual support (Chinese/English) | ✅ Done |
| S4 | First live run + output quality evaluation | ⏳ Next |
| S5 | Few-shot example library | 🔲 Planned |
| S6 | Automated evaluation pipeline | 🔲 Planned |
| S7 | DSPy prompt auto-optimization | 🔲 Planned |
| S8 | CrewAI AMP cloud deployment | 🔲 Planned |
| S9 | Web UI + real-time progress display | 🔲 Planned |
| S10 | Multi-language report output | 🔲 Planned |

---

## License

MIT License

---

*Built with 🦞 by 呆瓜军团 (Dumb Squad)*
