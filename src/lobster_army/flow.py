"""
龙虾军团 — CrewAI Flow 核心编排
用 @start / @listen / @router 替代手写状态机
"""

import json
import time
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from crewai import Crew, Task
from crewai.flow.flow import Flow, listen, start, router, and_
from anthropic import Anthropic

from .state import RunState, LobsterOutput
from .agents import (
    create_lobster_1, create_lobster_2, create_lobster_3,
    create_lobster_4, create_lobster_5,
    load_fewshot, build_anchor_prefix,
)
from .compression import compress_with_fallback, merge_and_validate
from .gate_check import check_semantic_consistency

PKG_DIR = Path(__file__).parent
haiku_client = Anthropic()


# ══════════════════════════════════════════════════════
# Prompt 构建辅助函数
# ══════════════════════════════════════════════════════

def build_l1_task_description(anchor: dict, idea: str) -> str:
    fewshot = load_fewshot("lobster_1")
    return (
        f"{build_anchor_prefix(anchor)}"
        f"用户的产品 Idea：\n{idea}\n\n"
        f"请严格按照 System Prompt 中的分析框架，交付完整的市场情报报告。\n\n"
        f"【四大模块 · 不可遗漏】\n"
        f"A. 市场规模量化（TAM/SAM/SOM 双方法交叉验证 + 中国市场独立章节）\n"
        f"B. 用户画像深度洞察（2-3 Persona × 10 维度 + 首选用户群标注）\n"
        f"C. 增长引擎分析（CAGR + 窗口期判断 Too Early/Just Right/Late）\n"
        f"D. 数据置信度标注（✅已验证 / ⚠️推算 / ❌未验证）\n\n"
        f"【验收红线】\n"
        f"- TAM 必须用 Top-down + Bottom-up 两种方法，差异 > 30% 必须解释\n"
        f"- 所有金额标注来源机构 + 年份\n"
        f"- 首选用户群必须有选择理由\n"
        f"- 中国市场独立分析（不是全球数据的子集）\n"
        f"- SOM 引用 1-2 个可类比公司的早期数据作为 benchmark\n\n"
        f"先在 <thinking> 标签内完成推理，再输出正式分析。\n"
        f"不确定的数据必须搜索验证，无法验证的标注 [未验证]。\n\n"
        f"{'参考示例：' + chr(10) + fewshot if fewshot else ''}"
    )


def build_l2_task_description(anchor: dict, idea: str) -> str:
    fewshot = load_fewshot("lobster_2")
    return (
        f"{build_anchor_prefix(anchor)}"
        f"用户的产品 Idea：\n{idea}\n\n"
        f"请严格按照 System Prompt 中的分析框架，交付完整的竞争情报报告。\n\n"
        f"【四大模块 · 不可遗漏】\n"
        f"A. 替代方案全景图（正式工具/半正式方案/手动方案/关联替代品，标注渗透率+满意度）\n"
        f"B. 竞品深度矩阵（5-8 竞品 × 12 维度，含直接竞品+间接替代+潜在进入者）\n"
        f"C. 战略分析工具（竞争力雷达图 + 战略群组地图 + 价值链弱点分析）\n"
        f"D. 机会与切入策略（市场空白 + CAC Benchmark + 3 个差异化方向）\n\n"
        f"【验收红线】\n"
        f"- 至少 5 个竞品，每个覆盖 12 维度中 ≥ 9 个\n"
        f"- 融资/定价/评分等关键数据必须搜索验证\n"
        f"- 包含竞争力雷达图（文字表格）和战略群组地图描述\n"
        f"- 3 个差异化方向每个有可行性/防御性/市场规模评分\n"
        f"- 明确推荐最优切入点\n"
        f"- CAC benchmark 至少 2 个同赛道数据点\n\n"
        f"先在 <thinking> 标签内完成推理，再输出正式分析。\n"
        f"所有竞品数据必须搜索验证。\n\n"
        f"{'参考示例：' + chr(10) + fewshot if fewshot else ''}"
    )


def build_l3_task_description(anchor: dict, combined_summary: dict) -> str:
    fewshot = load_fewshot("lobster_3")
    summary_text = json.dumps(combined_summary, ensure_ascii=False, indent=2)
    return (
        f"{build_anchor_prefix(anchor)}"
        f"上游数据（龙虾一+二的压缩摘要）：\n{summary_text}\n\n"
        f"你是枢纽龙虾 — 上游数据在你这里收束，下游所有决策基于你的定义展开。\n"
        f"请严格按照 System Prompt 中的分析框架，交付完整的产品定义报告。\n\n"
        f"【四大模块 · 不可遗漏】\n"
        f"A. 产品定位（三层金字塔 + ≤30字一句话定位 + 差异化声明模板完整填写）\n"
        f"B. 用户旅程（五阶段 × 7 要素 + Aha Moment 量化定义 + 流失点严重度标注）\n"
        f"C. 功能优先级（RICE 评分表含数据依据列 + MoSCoW 分类 + Won't-have 列表及排除理由）\n"
        f"D. MVP 定义（3-5 个核心功能的用户故事+验收标准 + North Star Metric + 演进路径+Go/No-Go）\n\n"
        f"【验收红线 — 检查点 B 校验依据】\n"
        f"- 一句话定位 ≤ 30 字，忠实于产品锚点（偏离将触发回滚重跑）\n"
        f"- 至少 5 处明确引用上游 L1/L2 数据作为决策依据\n"
        f"- MVP 不超过 5 个核心功能（克制！）\n"
        f"- 成功指标必须可量化（「D30 留存率 > 20%」，不是「用户增长」）\n"
        f"- 必须有 Won't-have 列表（明确说「不做什么」）\n\n"
        f"{'参考示例：' + chr(10) + fewshot if fewshot else ''}"
    )


def build_l4_task_description(anchor: dict, l3_content: str, combined_summary: dict) -> str:
    fewshot = load_fewshot("lobster_4")
    summary_text = json.dumps(combined_summary, ensure_ascii=False, indent=2)
    return (
        f"{build_anchor_prefix(anchor)}"
        f"龙虾三产品定义（全文）：\n{l3_content}\n\n"
        f"市场数据摘要：\n{summary_text}\n\n"
        f"请严格按照 System Prompt 中的分析框架，交付完整的技术实现方案。\n\n"
        f"【四大模块 · 不可遗漏】\n"
        f"A. 架构决策记录 ADR（≥3 个关键决策，每个标注所支撑的 L3 功能）\n"
        f"B. 三套完整技术蓝图：\n"
        f"   方案 A 精益 MVP：1-2人/4-8周/月运维<$200（完整技术栈+甘特图+成本明细+技术债务）\n"
        f"   方案 B 增长版：3-5人/支撑10x/月运维<$2K（含安全加固+CI/CD+API设计）\n"
        f"   方案 C 平台版：企业级架构/100x（含AI/多租户/合规/SRE+融资需求）\n"
        f"C. 三方案对比矩阵（≥6维度）+ Go/No-Go 演进路径\n"
        f"D. Top 5 技术风险预警（概率/影响/缓解方案/触发信号）\n\n"
        f"【验收红线】\n"
        f"- 每套方案的功能映射必须追溯到 L3 的 Must-have/Should-have\n"
        f"- 成本估算具体到月度金额范围（如 $150-220/月），不允许用「约」「大概」\n"
        f"- 方案 A 满足 1-2 人 4-8 周约束\n"
        f"- 必须标注技术债务和迁移成本\n\n"
        f"{'参考示例：' + chr(10) + fewshot if fewshot else ''}"
    )


def build_l5_task_description(anchor: dict, l3_content: str, l4_content: str, combined_summary: dict) -> str:
    fewshot = load_fewshot("lobster_5")
    summary_text = json.dumps(combined_summary, ensure_ascii=False, indent=2)
    return (
        f"{build_anchor_prefix(anchor)}"
        f"全部摘要：\n{summary_text}\n\n"
        f"龙虾三产品定义（全文）：\n{l3_content}\n\n"
        f"龙虾四技术方案（全文）：\n{l4_content}\n\n"
        f"你是龙虾军团的最终守门人和唯一反对派。你拥有全系统最多的上下文。\n"
        f"你的价值不是再写一份分析，而是找到前四只龙虾集体忽略的盲点。\n"
        f"请严格按照 System Prompt 中的分析框架，交付完整的风险报告。\n\n"
        f"【五大模块 · 不可遗漏】\n"
        f"A. Pre-Mortem 致命假设检验（5-7 个隐含假设，每个含验证方法+Plan B+风险等级矩阵）\n"
        f"B. 六维系统性风险矩阵（市场/竞争/技术/团队/资金/合规）+ Top 3 红色风险\n"
        f"C. 三级资金链断裂压力测试（温和50%超支/严重市场缩1/3/黑天鹅）含存活概率\n"
        f"D. 投资人尖锐问答（≥8 题，含隐含担忧+建议回答框架+最坏情况诚实回应）\n"
        f"E. 综合评估：健康度评分卡(6维) + 明确的 Kill/Pivot/Go 决策 + 一条最重要的建议\n\n"
        f"【验收红线】\n"
        f"- 每个风险必须配缓解方案（纯恐吓无价值）\n"
        f"- 缓解方案必须具体可执行（「花 $500 做 Landing Page 测试」而非「需要验证」）\n"
        f"- 综合评分在 3-8 之间（极端评分需极端证据）\n"
        f"- 必须给出明确的 Kill/Pivot/Go 决策\n\n"
        f"{'参考示例：' + chr(10) + fewshot if fewshot else ''}"
    )


# ══════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════

def run_single_lobster(agent, task_description: str, expected_output: str) -> str:
    """封装单只龙虾的 Crew 执行"""
    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    return str(result)


def generate_anchor_with_haiku(idea: str) -> Dict[str, Any]:
    """用 Haiku 从用户 Idea 生成结构化锚点"""
    response = haiku_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        temperature=0.2,
        messages=[{
            "role": "user",
            "content": (
                f"从以下产品 Idea 中提取结构化信息。只输出 JSON，不要其他文字。\n\n"
                f"Idea：{idea}\n\n"
                f"输出格式：\n"
                f'{{"name": "产品名称", "target_user": "目标用户", '
                f'"scenario": "使用场景", "core_problem": "要解决的核心问题", '
                f'"product_anchor": "为[用户]在[场景]下解决[问题]"}}'
            ),
        }],
    )
    import re
    raw = response.content[0].text.strip()
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if json_match:
        return json.loads(json_match.group())
    # Fallback: 简单模板
    return {
        "name": idea[:30],
        "target_user": "待定",
        "scenario": "待定",
        "core_problem": idea,
        "product_anchor": idea,
    }


# ══════════════════════════════════════════════════════
# 主 Flow
# ══════════════════════════════════════════════════════

class LobsterArmyFlow(Flow[RunState]):
    """龙虾军团主编排 Flow"""

    # ════════ Phase 0: 锚点生成 ════════
    @start()
    def generate_anchor(self):
        print("\n🎯 Phase 0: 生成产品锚点...")
        t0 = time.time()
        anchor = generate_anchor_with_haiku(self.state.idea)
        self.state.anchor = anchor
        self.state.phase = "parallel"
        self.state.persist()
        print(f"  ✅ 锚点生成完成: {anchor.get('product_anchor', '')}")
        return anchor

    # ════════ Phase 1: 并行龙虾一+二 ════════
    @listen(generate_anchor)
    def run_lobster_1(self):
        print("\n🦞 Phase 1a: 龙虾一 · 市场规模 + 用户洞察...")
        t0 = time.time()
        agent = create_lobster_1(self.state.anchor)
        desc = build_l1_task_description(self.state.anchor, self.state.idea)
        content = run_single_lobster(agent, desc, "投资级市场情报报告：双方法TAM/SAM/SOM + 中国市场独立章节 + 10维度用户画像 + 窗口期判断 + 数据置信度标注")
        self.state.L1 = LobsterOutput(
            content=content,
            duration_seconds=time.time() - t0,
            model="claude-sonnet-4-6",
        )
        self.state.save_lobster_output("lobster_1", self.state.L1)
        self.state.persist()
        print(f"  ✅ 龙虾一完成 ({time.time()-t0:.1f}s)")
        return content

    @listen(generate_anchor)  # ← 同时监听 anchor，与 L1 并行
    def run_lobster_2(self):
        print("\n🦞 Phase 1b: 龙虾二 · 竞品分析 + 市场空白...")
        t0 = time.time()
        agent = create_lobster_2(self.state.anchor)
        desc = build_l2_task_description(self.state.anchor, self.state.idea)
        content = run_single_lobster(agent, desc, "战略级竞争情报报告：替代方案全景图 + 5-8竞品12维度矩阵 + 竞争力雷达图 + 战略群组地图 + 3个差异化方向 + CAC benchmark")
        self.state.L2 = LobsterOutput(
            content=content,
            duration_seconds=time.time() - t0,
            model="claude-sonnet-4-6",
        )
        self.state.save_lobster_output("lobster_2", self.state.L2)
        self.state.persist()
        print(f"  ✅ 龙虾二完成 ({time.time()-t0:.1f}s)")
        return content

    # ════════ Phase 2: 独立压缩 + 合并 ════════
    @listen(run_lobster_1)
    def compress_l1(self):
        print("\n🗜️ Phase 2a: 压缩龙虾一输出...")
        if self.state.L1 is None:
            print("  ⚠️ 龙虾一输出为空，跳过压缩")
            return {}
        s1, cost = compress_with_fallback(self.state.L1.content, self.state.anchor, "summary_l1")
        self.state.summary_l1 = s1
        self.state.add_cost(cost)
        print(f"  ✅ 龙虾一压缩完成 (${cost:.4f})")
        return s1

    @listen(run_lobster_2)
    def compress_l2(self):
        print("\n🗜️ Phase 2b: 压缩龙虾二输出...")
        if self.state.L2 is None:
            print("  ⚠️ 龙虾二输出为空，跳过压缩")
            return {}
        s2, cost = compress_with_fallback(self.state.L2.content, self.state.anchor, "summary_l2")
        self.state.summary_l2 = s2
        self.state.add_cost(cost)
        print(f"  ✅ 龙虾二压缩完成 (${cost:.4f})")
        return s2

    @listen(and_(compress_l1, compress_l2))
    def merge_summaries(self):
        print("\n📋 Phase 2c: 合并摘要...")
        merged = merge_and_validate(
            self.state.summary_l1,
            self.state.summary_l2,
            self.state.anchor,
        )
        self.state.combined_summary = merged
        self.state.phase = "lobster_3"
        self.state.persist()

        # 保存 combined_summary.json
        run_path = PKG_DIR / "runs" / self.state.run_id
        run_path.mkdir(parents=True, exist_ok=True)
        (run_path / "combined_summary.json").write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("  ✅ 合并摘要完成")
        return merged

    # ════════ Phase 3: 龙虾三 + 语义检查点 ════════
    @listen(merge_summaries)
    def run_lobster_3(self):
        print("\n🦞 Phase 3: 龙虾三 · 产品定义 + 用户旅程（枢纽）...")
        t0 = time.time()
        agent = create_lobster_3(self.state.anchor)
        desc = build_l3_task_description(self.state.anchor, self.state.combined_summary)
        content = run_single_lobster(agent, desc, "产品定义报告：定位金字塔 + 五阶段旅程图 + RICE功能矩阵 + MVP规格(用户故事+验收标准) + North Star Metric + 演进路径")
        self.state.L3 = LobsterOutput(
            content=content,
            duration_seconds=time.time() - t0,
            model="claude-sonnet-4-6",
        )
        self.state.save_lobster_output("lobster_3", self.state.L3)
        self.state.persist()
        print(f"  ✅ 龙虾三完成 ({time.time()-t0:.1f}s)")
        return content

    @router(run_lobster_3)
    def gate_check(self):
        print("\n🚦 检查点 B: 语义一致性校验...")
        score, reason, cost = check_semantic_consistency(
            self.state.anchor,
            self.state.idea,
            self.state.L3.content,
        )
        self.state.gate_score = score
        self.state.add_cost(cost)
        print(f"  分数: {score}/10 — {reason}")

        if score >= 5:
            print("  ✅ 检查点通过")
            return "passed"
        elif self.state.gate_retries < 1:
            print("  ⚠️ 分数过低，准备重跑龙虾三...")
            return "retry"
        else:
            print("  ❌ 连续两次低于阈值，中止")
            return "abort"

    @listen("retry")
    def retry_lobster_3(self):
        print("\n🔄 重跑龙虾三 (temperature=0.5)...")
        self.state.gate_retries += 1
        t0 = time.time()
        agent = create_lobster_3(self.state.anchor, temperature=0.5)
        desc = build_l3_task_description(self.state.anchor, self.state.combined_summary)
        content = run_single_lobster(agent, desc, "产品定义报告：定位金字塔 + 五阶段旅程图 + RICE功能矩阵 + MVP规格(用户故事+验收标准) + North Star Metric + 演进路径")
        self.state.L3 = LobsterOutput(
            content=content,
            duration_seconds=time.time() - t0,
            model="claude-sonnet-4-6",
        )
        self.state.save_lobster_output("lobster_3", self.state.L3)
        self.state.persist()
        print(f"  ✅ 龙虾三重跑完成 ({time.time()-t0:.1f}s)")
        return content  # 会再次触发 gate_check router

    @listen("abort")
    def assemble_partial(self):
        print("\n⚠️ 生成部分报告...")
        self.state.phase = "partial"
        self.state.persist()
        report_content = self._build_partial_report()
        run_path = PKG_DIR / "runs" / self.state.run_id
        (run_path / "partial_report.md").write_text(report_content, encoding="utf-8")
        return report_content

    # ════════ Phase 4: 龙虾四 ════════
    @listen("passed")
    def run_lobster_4(self):
        print("\n🦞 Phase 4: 龙虾四 · 可行性方案...")
        t0 = time.time()
        agent = create_lobster_4(self.state.anchor)
        desc = build_l4_task_description(
            self.state.anchor,
            self.state.L3.content,
            self.state.combined_summary,
        )
        content = run_single_lobster(agent, desc, "技术蓝图：ADR决策记录 + 三套方案(精益MVP/增长版/平台版)完整技术栈+成本明细 + 对比矩阵 + Go/No-Go路径 + 技术风险Top5")
        self.state.L4 = LobsterOutput(
            content=content,
            duration_seconds=time.time() - t0,
            model="claude-sonnet-4-6",
        )
        self.state.save_lobster_output("lobster_4", self.state.L4)
        self.state.persist()
        print(f"  ✅ 龙虾四完成 ({time.time()-t0:.1f}s)")
        return content

    # ════════ Phase 5: 龙虾五 ════════
    @listen(run_lobster_4)
    def run_lobster_5(self):
        print("\n🦞 Phase 5: 龙虾五 · 风险分析（深度批判者）...")
        t0 = time.time()
        agent = create_lobster_5(self.state.anchor)
        desc = build_l5_task_description(
            self.state.anchor,
            self.state.L3.content,
            self.state.L4.content,
            self.state.combined_summary,
        )
        content = run_single_lobster(agent, desc, "风险报告：Pre-Mortem假设检验 + 六维风险矩阵 + 三级压力测试 + 投资人8题问答 + 健康度评分卡 + Kill/Pivot/Go决策")
        self.state.L5 = LobsterOutput(
            content=content,
            duration_seconds=time.time() - t0,
            model="claude-sonnet-4-6",
        )
        self.state.save_lobster_output("lobster_5", self.state.L5)
        self.state.persist()
        print(f"  ✅ 龙虾五完成 ({time.time()-t0:.1f}s)")
        return content

    # ════════ Phase 6: 拼接报告 ════════
    @listen(run_lobster_5)
    def assemble_report(self):
        print("\n📊 Phase 6: 拼接最终报告...")
        report = self._build_full_report()
        meta = self._build_meta()

        run_path = PKG_DIR / "runs" / self.state.run_id
        run_path.mkdir(parents=True, exist_ok=True)
        (run_path / "final_report.md").write_text(report, encoding="utf-8")
        (run_path / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self.state.phase = "done"
        self.state.persist()
        print(f"\n{'='*60}")
        print(f"✅ 龙虾军团分析完成！")
        print(f"📄 报告：runs/{self.state.run_id}/final_report.md")
        print(f"💰 总成本：${self.state.total_cost:.4f}")
        print(f"{'='*60}")
        return report

    # ══════════════════════════════════════════════════════
    # 报告构建
    # ══════════════════════════════════════════════════════

    def _build_full_report(self) -> str:
        anchor_text = self.state.anchor.get("product_anchor", self.state.idea)
        sections = [
            f"# 🦞 龙虾军团产品分析报告\n",
            f"**产品定位：** {anchor_text}\n",
            f"**分析日期：** {datetime.now().strftime('%Y-%m-%d')}\n",
            f"**Run ID：** {self.state.run_id}\n",
            f"\n---\n",
            f"## 1. 市场分析\n\n{self.state.L1.content if self.state.L1 else '[龙虾一输出不可用]'}\n",
            f"\n---\n",
            f"## 2. 竞争格局\n\n{self.state.L2.content if self.state.L2 else '[龙虾二输出不可用]'}\n",
            f"\n---\n",
            f"## 3. 产品定义\n\n{self.state.L3.content if self.state.L3 else '[龙虾三输出不可用]'}\n",
            f"\n---\n",
            f"## 4. 实现方案\n\n{self.state.L4.content if self.state.L4 else '[龙虾四输出不可用]'}\n",
            f"\n---\n",
            f"## 5. 风险与融资\n\n{self.state.L5.content if self.state.L5 else '[龙虾五输出不可用]'}\n",
        ]
        return "\n".join(sections)

    def _build_partial_report(self) -> str:
        return (
            f"# ⚠️ 龙虾军团部分报告（检查点 B 未通过）\n\n"
            f"**原因：** 龙虾三产品定义与原始 Idea 语义偏离过大（得分 {self.state.gate_score}/10）\n"
            f"**建议：** 调整 Idea 描述后重新运行\n\n"
            f"## 已完成的分析\n\n"
            f"### 市场分析\n{self.state.L1.content if self.state.L1 else '[不可用]'}\n\n"
            f"### 竞争格局\n{self.state.L2.content if self.state.L2 else '[不可用]'}\n"
        )

    def _build_meta(self) -> dict:
        completeness = sum(1 for x in [self.state.L1, self.state.L2, self.state.L3, self.state.L4, self.state.L5] if x is not None)
        return {
            "run_id": self.state.run_id,
            "idea": self.state.idea,
            "status": self.state.phase,
            "completeness": f"{completeness}/5",
            "gate_score": self.state.gate_score,
            "total_cost": round(self.state.total_cost, 4),
            "started_at": self.state.started_at,
            "finished_at": datetime.now().isoformat(),
            "errors": self.state.errors,
            "prompt_version": self.state.prompt_version,
        }
