"""
龙虾军团 — 五只龙虾 Agent 定义 (v2.0 世界一流团队标准)
每只龙虾 = 一个 CrewAI Agent，对应 CRISPE 框架的 Capacity / Role / Personality
设计理念：硬件级验收标准 + 工业级专业分工
"""

from crewai import Agent, LLM
from pathlib import Path
from typing import Dict, Any, Optional
import json
import yaml


def load_config() -> dict:
    """加载全局配置"""
    config_path = Path("config.yaml")
    if config_path.exists():
        return yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return {}


def get_language() -> str:
    """获取当前语言设置"""
    config = load_config()
    return config.get("output", {}).get("language", "zh")


def load_prompt(lobster_id: str, lang: str = None) -> str:
    """加载 System Prompt 文件（支持双语）

    lang: "zh" → system.txt, "en" → system_en.txt
    默认读取 config.yaml 中的 output.language 设置
    """
    if lang is None:
        lang = get_language()

    suffix = "_en" if lang == "en" else ""
    prompt_path = Path(f"prompts/{lobster_id}/system{suffix}.txt")

    # 回退：如果英文版不存在，使用中文版
    if not prompt_path.exists() and lang == "en":
        prompt_path = Path(f"prompts/{lobster_id}/system.txt")

    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return f"You are {lobster_id}, a product analysis expert." if lang == "en" else f"你是{lobster_id}，一个产品分析专家。"


def load_fewshot(lobster_id: str) -> str:
    """加载 Few-shot 示例并格式化为文本"""
    fewshot_path = Path(f"prompts/{lobster_id}/fewshot.json")
    if fewshot_path.exists():
        shots = json.loads(fewshot_path.read_text(encoding="utf-8"))
        formatted = []
        for i, shot in enumerate(shots, 1):
            formatted.append(f"=== 示例 {i} ===\n{shot.get('content', '')}")
        return "\n\n".join(formatted)
    return ""


def get_llm(model_key: str = "sonnet", temperature: Optional[float] = None) -> LLM:
    """获取 LLM 实例"""
    config = load_config()
    model_config = config.get("models", {}).get(model_key, {})
    model_name = model_config.get("name", "anthropic/claude-sonnet-4-6")
    temp = temperature if temperature is not None else model_config.get("temperature", 0.3)
    return LLM(model=model_name, temperature=temp)


def build_anchor_prefix(anchor: Dict[str, Any], lang: str = None) -> str:
    """构建注入每只龙虾 Prompt 开头的锚点前缀（支持双语）"""
    if lang is None:
        lang = get_language()

    if lang == "en":
        return (
            f"╔══════════════════════════════════════════════════════════╗\n"
            f"║  Product Anchor — All analysis must revolve around this ║\n"
            f"╚══════════════════════════════════════════════════════════╝\n"
            f"Product Name: {anchor.get('name', 'N/A')}\n"
            f"Target User: {anchor.get('target_user', 'N/A')}\n"
            f"Scenario: {anchor.get('scenario', 'N/A')}\n"
            f"Core Problem: {anchor.get('core_problem', 'N/A')}\n"
            f"One-liner: {anchor.get('product_anchor', 'N/A')}\n"
            f"{'═'*58}\n\n"
        )
    return (
        f"╔══════════════════════════════════════════════════════╗\n"
        f"║  产品锚点 — 所有分析必须围绕此锚点展开，不得偏离  ║\n"
        f"╚══════════════════════════════════════════════════════╝\n"
        f"产品名称：{anchor.get('name', 'N/A')}\n"
        f"目标用户：{anchor.get('target_user', 'N/A')}\n"
        f"使用场景：{anchor.get('scenario', 'N/A')}\n"
        f"核心问题：{anchor.get('core_problem', 'N/A')}\n"
        f"一句话定位：{anchor.get('product_anchor', 'N/A')}\n"
        f"{'═'*55}\n\n"
    )


# ══════════════════════════════════════════════════════
# L1：首席市场情报官 (Chief Market Intelligence Officer)
# 专业：麦肯锡级行业分析 × Gartner级数据定量 × IDEO级用户洞察
# ══════════════════════════════════════════════════════
def create_lobster_1(anchor: Dict[str, Any], temperature: Optional[float] = None) -> Agent:
    config = load_config().get("lobsters", {}).get("lobster_1", {})
    system_prompt = load_prompt("lobster_1")
    backstory = build_anchor_prefix(anchor) + system_prompt

    return Agent(
        role="首席市场情报官 (CMIO) — 麦肯锡合伙人级行业分析 + Gartner首席分析师级数据定量 + IDEO人种志研究员级用户洞察",
        goal=(
            "交付一份投资级市场情报报告。核心交付物：\n"
            "1. 双方法交叉验证的 TAM/SAM/SOM 估算（Top-down + Bottom-up）\n"
            "2. 中国市场独立分析章节（独立 TAM/SAM + 政策环境 + 本土替代品）\n"
            "3. 10 维度刻画的用户画像（2-3 个 Persona），标注首选用户群及选择理由\n"
            "4. 市场窗口期判断（Too Early / Just Right / Late）\n"
            "5. 数据置信度全标注（✅已验证 / ⚠️推算 / ❌未验证）"
        ),
        backstory=backstory,
        llm=get_llm("sonnet", temperature),
        max_iter=5,
        max_tokens=config.get("max_tokens", 4500),
        verbose=True,
    )


# ══════════════════════════════════════════════════════
# L2：首席竞争情报官 (Chief Competitive Intelligence Officer)
# 专业：CB Insights级竞品追踪 × 贝恩级战略咨询 × Product Hunt级用户声音
# ══════════════════════════════════════════════════════
def create_lobster_2(anchor: Dict[str, Any], temperature: Optional[float] = None) -> Agent:
    config = load_config().get("lobsters", {}).get("lobster_2", {})
    system_prompt = load_prompt("lobster_2")
    backstory = build_anchor_prefix(anchor) + system_prompt

    return Agent(
        role="首席竞争情报官 (CCIO) — CB Insights首席分析师级竞品追踪 + 贝恩战略咨询级五力分析 + G2用户声音挖掘",
        goal=(
            "交付一份战略级竞争情报报告。核心交付物：\n"
            "1. 替代方案全景图（正式工具 / 半正式方案 / 手动方案 / 关联替代品）\n"
            "2. 5-8 个竞品的 12 维度深度矩阵（融资/定价/评分/弱点等）\n"
            "3. 竞争力雷达图 + 战略群组地图 + 价值链弱点分析\n"
            "4. 3 个差异化切入方向（含可行性/防御性/市场规模评分）\n"
            "5. CAC Benchmark 数据（至少 2 个同赛道数据点）\n"
            "6. 明确推荐最优切入点"
        ),
        backstory=backstory,
        llm=get_llm("sonnet", temperature),
        max_iter=5,
        max_tokens=config.get("max_tokens", 4500),
        verbose=True,
    )


# ══════════════════════════════════════════════════════
# L3：首席产品官 (CPO) — 枢纽龙虾
# 专业：Superhuman级产品定义 × IDEO级体验设计 × YC级产品直觉
# ══════════════════════════════════════════════════════
def create_lobster_3(anchor: Dict[str, Any], temperature: Optional[float] = None) -> Agent:
    config = load_config().get("lobsters", {}).get("lobster_3", {})
    system_prompt = load_prompt("lobster_3")
    backstory = build_anchor_prefix(anchor) + system_prompt

    return Agent(
        role="首席产品官 (CPO) — Superhuman级产品定义 + IDEO设计策略师级体验设计 + YC合伙人级产品直觉 · 枢纽龙虾",
        goal=(
            "交付一份可直接用于开发启动的产品定义文档。核心交付物：\n"
            "1. 产品定位三层金字塔 + ≤30字一句话定位 + 差异化定位声明\n"
            "2. 五阶段用户旅程图（7 要素/阶段）+ Aha Moment 量化定义\n"
            "3. RICE + MoSCoW 混合功能优先级矩阵（每项有数据依据列）\n"
            "4. MVP 功能规格（用户故事 + 验收标准 + 边界条件）· 3-5 个核心功能\n"
            "5. North Star Metric + 支撑指标 + 护栏指标\n"
            "6. MVP→V1→V2 演进路径 + Go/No-Go 节点\n"
            "7. 所有产品决策至少 5 处引用上游 L1/L2 数据"
        ),
        backstory=backstory,
        llm=get_llm("sonnet", temperature),
        max_iter=3,
        max_tokens=config.get("max_tokens", 4000),
        verbose=True,
    )


# ══════════════════════════════════════════════════════
# L4：首席技术官 (CTO) + 首席架构师
# 专业：Stripe级架构 × AWS SA Professional级基础设施 × YC TDD级技术评审
# ══════════════════════════════════════════════════════
def create_lobster_4(anchor: Dict[str, Any], temperature: Optional[float] = None) -> Agent:
    config = load_config().get("lobsters", {}).get("lobster_4", {})
    system_prompt = load_prompt("lobster_4")
    backstory = build_anchor_prefix(anchor) + system_prompt

    return Agent(
        role="首席技术官 + 首席架构师 (CTO/CA) — Stripe级技术架构 + AWS SA Professional级基础设施 + YC Technical Due Diligence级评审",
        goal=(
            "交付一份可直接指导工程团队执行的技术蓝图。核心交付物：\n"
            "1. Top 5 架构决策记录 (ADR) — 每个标注所支撑的 L3 功能\n"
            "2. 方案 A（精益MVP）：1-2人/4-8周/月运维<$200，完整技术栈+甘特图+成本明细\n"
            "3. 方案 B（增长版）：3-5人团队/10x扩展/月运维<$2K，含安全加固+CI/CD\n"
            "4. 方案 C（平台版）：企业级架构/100x规模/含AI组件+多租户+合规\n"
            "5. 三方案对比矩阵（≥6维度）+ Go/No-Go演进路径\n"
            "6. Top 5 技术风险预警（含概率/影响/缓解方案/触发信号）"
        ),
        backstory=backstory,
        llm=get_llm("sonnet", temperature),
        max_iter=3,
        max_tokens=config.get("max_tokens", 5500),
        verbose=True,
    )


# ══════════════════════════════════════════════════════
# L5：首席风控官 (CRO) + 红队队长 — 深度批判者
# 专业：Sequoia级投资审查 × 桥水级风险分析 × 军事红队级对抗思维
# ══════════════════════════════════════════════════════
def create_lobster_5(anchor: Dict[str, Any], temperature: Optional[float] = None) -> Agent:
    config = load_config().get("lobsters", {}).get("lobster_5", {})
    system_prompt = load_prompt("lobster_5")
    backstory = build_anchor_prefix(anchor) + system_prompt

    return Agent(
        role="首席风控官 + 红队队长 (CRO/RTL) — Sequoia合伙人级投资审查 + 桥水风险分析师级系统思维 + 军事红队指挥官级对抗性思维",
        goal=(
            "交付一份能让创业项目在更恶劣条件下存活的风险报告。核心交付物：\n"
            "1. Pre-Mortem 致命假设检验：5-7 个隐含假设（含验证方法+Plan B+风险等级）\n"
            "2. 六维系统性风险矩阵（市场/竞争/技术/团队/资金/合规）+ 红色风险 Top 3\n"
            "3. 三级资金链断裂压力测试（温和/严重/黑天鹅）含存活概率\n"
            "4. 投资人尖锐问答 8 题（含隐含担忧+建议回答框架+最坏情况诚实回应）\n"
            "5. 健康度评分卡（6 维度加权评分）\n"
            "6. 明确的 Kill/Pivot/Go 决策建议\n"
            "7. 一条最重要的、具体可执行的生存建议"
        ),
        backstory=backstory,
        llm=get_llm("sonnet", temperature),
        max_iter=3,
        max_tokens=config.get("max_tokens", 5000),
        verbose=True,
    )
