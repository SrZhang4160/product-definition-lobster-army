"""
龙虾军团 v4.0 — 交互式产品工作坊
自由选择龙虾 + 询问细节/补充信息反馈 + 中英切换 + 历史记录

启动：streamlit run app.py
"""

import streamlit as st
import json
import os
import re
import sys
import base64
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

# ══════════════════════════════════════════════════════
# 路径 & 环境（纯 Python，不调用任何 st.*）
# ══════════════════════════════════════════════════════
APP_DIR = Path(__file__).parent
PROJECT_ROOT = APP_DIR.parent
HISTORY_DIR = APP_DIR / "history"
HISTORY_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# 加载 .env
for _env_path in [APP_DIR / ".env", PROJECT_ROOT / ".env"]:
    if _env_path.exists():
        for _line in _env_path.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())
        break

# ══════════════════════════════════════════════════════
# set_page_config 必须是第一个 st.* 调用
# ══════════════════════════════════════════════════════
st.set_page_config(page_title="Lobster Army", page_icon="🦞", layout="wide")

# Streamlit Cloud Secrets（仅在 secrets.toml 存在时才访问，避免 warning）
_secrets_paths = [
    Path.home() / ".streamlit" / "secrets.toml",
    APP_DIR / ".streamlit" / "secrets.toml",
]
if any(p.exists() for p in _secrets_paths):
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets["ANTHROPIC_API_KEY"])
        if "GITHUB_TOKEN" in st.secrets:
            os.environ.setdefault("GITHUB_TOKEN", st.secrets["GITHUB_TOKEN"])
        if "GITHUB_REPO" in st.secrets:
            os.environ.setdefault("GITHUB_REPO", st.secrets["GITHUB_REPO"])
    except Exception:
        pass

# ══════════════════════════════════════════════════════
# 国际化
# ══════════════════════════════════════════════════════
I18N = {
    "zh": {
        "app_title": "呆瓜军团 — 产品分析工作坊",
        "app_subtitle": "输入你的产品 Idea，5 只呆瓜将逐步为你做深度分析。\n自由选择任意呆瓜，审阅、讨论、补充，满意后确认。",
        "sidebar_title": "呆瓜军团",
        "sidebar_caption": "交互式产品工作坊 v4.0",
        "current_analysis": "当前分析",
        "new_analysis": "新建分析",
        "history": "历史记录",
        "no_history": "还没有历史记录",
        "input_idea": "你的产品 Idea",
        "input_placeholder": "例如：一个帮助独立开发者自动生成 landing page 的 AI 工具\n\n写得越详细，呆瓜们分析得越精准。可以包括：目标用户、核心场景、你观察到的痛点等。",
        "start_analysis": "开始分析",
        "examples_title": "示例 Ideas",
        "anchor": "产品锚点",
        "run_analysis": "运行分析",
        "confirm_report": "确认报告",
        "regenerate": "重新生成",
        "back_to_dashboard": "返回总览",
        "tab_report": "分析报告",
        "tab_ask": "询问细节",
        "tab_supplement": "补充信息",
        "ask_placeholder": "对报告有疑问？输入你想了解的细节...",
        "supplement_placeholder": "输入你要补充的信息（如已有数据、行业背景、团队情况等）...",
        "supplement_update": "根据补充信息更新报告",
        "download_md": "下载报告 (MD)",
        "download_json": "下载数据 (JSON)",
        "summary_title": "完整分析报告",
        "view_summary": "查看汇总报告",
        "summary_discuss": "和呆瓜军团继续讨论",
        "summary_discuss_hint": "报告已汇总。继续追问任何问题，所有呆瓜的分析都在上下文中。",
        "summary_input": "对报告有任何问题？",
        "thinking": "思考中...",
        "analyzing": "正在分析... 这可能需要 30-60 秒",
        "generating_anchor": "生成产品锚点...",
        "updating_report": "根据补充信息更新报告...",
        "not_started": "未开始",
        "completed": "已完成",
        "confirmed": "已确认",
        "cost_hint": "每只呆瓜约 $0.05-0.10\n完整分析约 $0.40-0.50",
        "lang_toggle": "English",
        "prev_reports_hint": "已有报告将自动引用",
        "mode_sequential": "顺序模式（推荐）",
        "mode_free": "自由模式",
        "mode_seq_desc": "按产品开发流程：市场 > 竞品 > 产品 > 技术 > 风控，每步自动引用上游报告",
        "mode_free_desc": "自由选择任意呆瓜，适合只需要某个维度的分析",
        "next_step": "下一步",
        "skip_step": "跳过此步",
        "step_progress": "步骤",
        "examples": [
            "针对成年人的桌面干眼检测/缓解装置，带情绪关怀功能",
            "面向中小型餐厅的 AI 菜单定价优化系统",
            "帮助独立音乐人分发和推广音乐的平台",
        ],
        "lobsters": [
            {"id": "L1", "name": "呆瓜1 · 市场情报官 (CMIO)", "short": "市场分析",
             "desc": "TAM/SAM/SOM 市场规模、用户画像、增长引擎"},
            {"id": "L2", "name": "呆瓜2 · 竞争情报官 (CCIO)", "short": "竞品分析",
             "desc": "竞品矩阵、市场空白、差异化方向"},
            {"id": "L3", "name": "呆瓜3 · 产品官 (CPO)", "short": "产品定义",
             "desc": "定位金字塔、用户旅程、MVP 功能优先级"},
            {"id": "L4", "name": "呆瓜4 · 技术官 (CTO)", "short": "技术方案",
             "desc": "软硬件架构决策、元器件选型、技术蓝图与成本"},
            {"id": "L5", "name": "呆瓜5 · 风控官 (CRO)", "short": "风险评估",
             "desc": "致命假设检验、压力测试、Kill/Pivot/Go"},
        ],
    },
    "en": {
        "app_title": "Lobster Army — Product Analysis Workshop",
        "app_subtitle": "Enter your product idea. 5 AI lobsters will provide deep analysis.\nPick any lobster freely. Review, discuss, supplement, then confirm.",
        "sidebar_title": "Lobster Army",
        "sidebar_caption": "Interactive Workshop v4.0",
        "current_analysis": "Current Analysis",
        "new_analysis": "New Analysis",
        "history": "History",
        "no_history": "No history yet",
        "input_idea": "Your Product Idea",
        "input_placeholder": "E.g.: An AI tool that auto-generates landing pages for indie developers\n\nThe more detail you provide, the better the analysis. Include: target users, core scenarios, pain points you've observed.",
        "start_analysis": "Start Analysis",
        "examples_title": "Example Ideas",
        "anchor": "Product Anchor",
        "run_analysis": "Run Analysis",
        "confirm_report": "Confirm Report",
        "regenerate": "Regenerate",
        "back_to_dashboard": "Back to Dashboard",
        "tab_report": "Report",
        "tab_ask": "Ask Details",
        "tab_supplement": "Add Info",
        "ask_placeholder": "Questions about the report? Ask for details...",
        "supplement_placeholder": "Add context (existing data, industry background, team info, etc.)...",
        "supplement_update": "Update Report with New Info",
        "download_md": "Download Report (MD)",
        "download_json": "Download Data (JSON)",
        "summary_title": "Full Analysis Report",
        "view_summary": "View Summary Report",
        "summary_discuss": "Continue Discussion with Lobster Army",
        "summary_discuss_hint": "All reports are consolidated. Ask any follow-up questions.",
        "summary_input": "Any questions about the report?",
        "thinking": "Thinking...",
        "analyzing": "Analyzing... this may take 30-60 seconds",
        "generating_anchor": "Generating product anchor...",
        "updating_report": "Updating report with supplementary info...",
        "not_started": "Not started",
        "completed": "Completed",
        "confirmed": "Confirmed",
        "cost_hint": "~$0.05-0.10 per lobster\n~$0.40-0.50 for full analysis",
        "lang_toggle": "中文",
        "prev_reports_hint": "Available reports will be auto-referenced",
        "mode_sequential": "Sequential (Recommended)",
        "mode_free": "Free Pick",
        "mode_seq_desc": "Follow product dev flow: Market > Competitive > Product > Tech > Risk. Each step auto-references upstream reports.",
        "mode_free_desc": "Pick any lobster freely. Best for analyzing a single dimension.",
        "next_step": "Next Step",
        "skip_step": "Skip",
        "step_progress": "Step",
        "examples": [
            "A desktop dry-eye detection/relief device for adults with emotional care features",
            "AI-powered menu pricing optimization for small restaurants",
            "A platform for indie musicians to distribute and promote music",
        ],
        "lobsters": [
            {"id": "L1", "name": "Lobster 1 · Chief Market Intelligence Officer", "short": "Market Analysis",
             "desc": "TAM/SAM/SOM market sizing, user personas, growth engines"},
            {"id": "L2", "name": "Lobster 2 · Chief Competitive Intelligence Officer", "short": "Competitive Analysis",
             "desc": "Competitor matrix, market gaps, differentiation"},
            {"id": "L3", "name": "Lobster 3 · Chief Product Officer", "short": "Product Definition",
             "desc": "Positioning pyramid, user journey, MVP feature prioritization"},
            {"id": "L4", "name": "Lobster 4 · Chief Technology Officer", "short": "Technical Plan",
             "desc": "HW/SW architecture, component selection, technical blueprint & cost"},
            {"id": "L5", "name": "Lobster 5 · Chief Risk Officer", "short": "Risk Assessment",
             "desc": "Fatal assumption tests, stress tests, Kill/Pivot/Go"},
        ],
    },
}


def t(key: str) -> str:
    """获取当前语言的文本"""
    lang = st.session_state.get("lang", "zh")
    return I18N[lang].get(key, key)


def get_lobsters() -> list:
    lang = st.session_state.get("lang", "zh")
    return I18N[lang]["lobsters"]


def get_examples() -> list:
    lang = st.session_state.get("lang", "zh")
    return I18N[lang]["examples"]


# ══════════════════════════════════════════════════════
# 初始化
# ══════════════════════════════════════════════════════
client = Anthropic()

DEFAULTS = {
    "page": "input",       # input / dashboard / lobster / summary
    "active_lobster": None,  # "L1" ~ "L5"
    "mode": "sequential",  # "sequential" or "free"
    "seq_step": 0,         # 顺序模式当前步骤 0-4 (对应 L1-L5)
    "idea": "",
    "reports": {},
    "confirmed": {},
    "chat_histories": {},
    "supplement_histories": {},
    "anchor": {},
    "final_chat": [],
    "lang": "zh",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════
# 历史记录
# ══════════════════════════════════════════════════════

def _push_to_github(filename: str, content: str):
    """通过 GitHub API 将报告文件 push 到仓库的 reports/ 目录"""
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPO", "")  # 格式: "owner/repo"
    if not token or not repo:
        return  # 没有配置则跳过

    api_url = f"https://api.github.com/repos/{repo}/contents/reports/{filename}"
    payload = json.dumps({
        "message": f"report: {filename}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": os.environ.get("GITHUB_BRANCH", "main"),
    }).encode("utf-8")

    req = urllib.request.Request(api_url, data=payload, method="PUT", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass  # push 失败不影响主流程


def save_to_history():
    anchor_name = st.session_state.anchor.get("name", "unnamed")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = re.sub(r'[^\w\u4e00-\u9fff._-]', '_', f"{ts}_{anchor_name}.json")
    data = {
        "idea": st.session_state.idea,
        "anchor": st.session_state.anchor,
        "reports": st.session_state.reports,
        "confirmed": st.session_state.confirmed,
        "chat_histories": st.session_state.chat_histories,
        "supplement_histories": st.session_state.supplement_histories,
        "final_chat": st.session_state.final_chat,
        "saved_at": datetime.now().isoformat(),
        "version": "4.0",
    }
    content = json.dumps(data, ensure_ascii=False, indent=2)

    # 本地保存
    (HISTORY_DIR / filename).write_text(content, encoding="utf-8")

    # 自动 push 到 GitHub（云端部署时）
    _push_to_github(filename, content)

    return filename


def load_history(filename: str) -> dict:
    path = HISTORY_DIR / filename
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def list_history() -> list:
    files = sorted(HISTORY_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    result = []
    for f in files[:20]:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "filename": f.name,
                "idea": d.get("idea", "")[:50],
                "anchor_name": d.get("anchor", {}).get("name", "?"),
                "saved_at": d.get("saved_at", ""),
                "num_reports": len(d.get("reports", {})),
            })
        except Exception:
            continue
    return result


def restore_session(data: dict):
    st.session_state.idea = data.get("idea", "")
    st.session_state.anchor = data.get("anchor", {})
    st.session_state.reports = data.get("reports", {})
    st.session_state.confirmed = data.get("confirmed", {lid: True for lid in data.get("reports", {})})
    st.session_state.chat_histories = data.get("chat_histories", {})
    st.session_state.supplement_histories = data.get("supplement_histories", {})
    st.session_state.final_chat = data.get("final_chat", [])
    st.session_state.page = "dashboard"
    st.session_state.active_lobster = None


# ══════════════════════════════════════════════════════
# Prompt 加载
# ══════════════════════════════════════════════════════

def load_system_prompt(lobster_id: str) -> str:
    for base in [APP_DIR / "prompts", PROJECT_ROOT / "src" / "lobster_army" / "prompts"]:
        path = base / f"lobster_{lobster_id}" / "system.txt"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return f"你是呆瓜{lobster_id}，一个专业的产品分析专家。请用中文输出专业分析报告。"


def load_anchor_prompt() -> str:
    for base in [APP_DIR / "prompts", PROJECT_ROOT / "src" / "lobster_army" / "prompts"]:
        path = base / "anchor" / "system.txt"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return "从用户的产品 Idea 中提取结构化锚点信息。只输出 JSON。"


# ══════════════════════════════════════════════════════
# 核心分析函数
# ══════════════════════════════════════════════════════

def generate_anchor(idea: str) -> dict:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=300,
        system=load_anchor_prompt(),
        messages=[{"role": "user", "content": f"产品 Idea：{idea}"}],
    )
    text = resp.content[0].text
    try:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return {"product_anchor": idea, "raw": text}


COMPRESSION_FOCUS = {
    2: "市场规模数字(TAM/SAM/SOM)、目标用户画像、核心使用场景、增长驱动力",
    3: "市场规模与增长数据、竞品格局与空白机会、用户核心痛点、差异化方向",
    4: "产品定位、MVP功能清单与优先级、核心用户旅程、技术相关的产品需求",
    5: "市场规模与验证程度、竞争壁垒评估、产品关键假设、技术架构选型与成本、所有已识别的风险点",
}


@st.cache_data(ttl=3600, show_spinner=False)
def compress_report(report: str, target_num: int, source_name: str) -> str:
    focus = COMPRESSION_FOCUS.get(target_num, "关键结论、核心数据、主要发现")
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=800,
        system=f"""你是一个报告压缩器。将分析报告提炼为结构化摘要。
压缩规则：保留关键数据点、核心结论、来源标注 [来源:] [推算:]，去除冗余，不超过 600 字。
本次重点：{focus}""",
        messages=[{"role": "user", "content": f"压缩 {source_name} 的报告：\n\n{report}"}],
    )
    return resp.content[0].text


def _build_context(idea: str, anchor: dict, prev_reports: dict, lobster_num: int) -> str:
    lobsters = get_lobsters()
    parts = [
        f"## 产品锚点\n{json.dumps(anchor, ensure_ascii=False, indent=2)}",
        f"\n## 原始 Idea\n{idea}",
    ]
    for lid, report in prev_reports.items():
        info = next((l for l in lobsters if l["id"] == lid), None)
        if not info:
            continue
        if lobster_num >= 3 and len(prev_reports) >= 2:
            compressed = compress_report(report, lobster_num, info["name"])
            parts.append(f"\n## {info['name']} 关键结论（压缩摘要）\n{compressed}")
        else:
            parts.append(f"\n## {info['name']} 已确认报告\n{report[:3000]}")
    return "\n".join(parts)


def run_lobster(lobster_num: int, idea: str, anchor: dict, prev_reports: dict) -> str:
    lang = st.session_state.get("lang", "zh")
    lang_instruction = "\n\n请用中文输出报告。" if lang == "zh" else "\n\nPlease output the report in English."
    context = _build_context(idea, anchor, prev_reports, lobster_num)
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=5000,
        system=load_system_prompt(str(lobster_num)) + lang_instruction,
        messages=[{"role": "user", "content": context + "\n\n请根据以上信息，输出你的完整专业分析报告。"}],
    )
    return resp.content[0].text


def chat_with_lobster(lobster_num: int, report: str, chat_history: list, user_msg: str, idea: str, anchor: dict) -> str:
    sys_prompt = load_system_prompt(str(lobster_num)) + f"""

## 当前上下文
你已经输出了一份报告，用户正在和你讨论。请根据问题给出专业回答。

## 产品锚点
{json.dumps(anchor, ensure_ascii=False, indent=2)}

## 你的报告
{report[:4000]}
"""
    messages = [{"role": m["role"], "content": m["content"]} for m in chat_history]
    messages.append({"role": "user", "content": user_msg})
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=3000,
        system=sys_prompt, messages=messages,
    )
    return resp.content[0].text


def supplement_report(lobster_num: int, original_report: str, supplement: str, idea: str, anchor: dict, prev_reports: dict) -> str:
    """根据用户补充信息更新报告"""
    lang = st.session_state.get("lang", "zh")
    lang_instruction = "\n\n请用中文输出报告。" if lang == "zh" else "\n\nPlease output the report in English."
    context = _build_context(idea, anchor, prev_reports, lobster_num)
    sys_prompt = load_system_prompt(str(lobster_num)) + lang_instruction
    sys_prompt += f"""

## 重要：用户补充信息
用户提供了以下补充信息，请在新版报告中充分吸收这些信息，更新相关分析和结论。
如果补充信息与原报告有冲突，以用户补充为准。

补充内容：
{supplement}
"""
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=5000,
        system=sys_prompt,
        messages=[{"role": "user", "content": context + f"\n\n## 原报告（需更新）\n{original_report[:3000]}\n\n请输出更新后的完整专业分析报告。"}],
    )
    return resp.content[0].text


# ══════════════════════════════════════════════════════
# 侧栏
# ══════════════════════════════════════════════════════
with st.sidebar:
    # 语言切换
    if st.button(t("lang_toggle"), use_container_width=True):
        st.session_state.lang = "en" if st.session_state.lang == "zh" else "zh"
        st.rerun()

    st.title(t("sidebar_title"))
    st.caption(t("sidebar_caption"))
    st.divider()

    if st.session_state.idea:
        st.markdown(f"**{t('current_analysis')}:** {st.session_state.idea[:40]}...")

        # 龙虾状态总览
        lobsters = get_lobsters()
        for lb in lobsters:
            lid = lb["id"]
            if lid in st.session_state.confirmed:
                status = f"  [{t('confirmed')}]"
            elif lid in st.session_state.reports:
                status = f"  [{t('completed')}]"
            else:
                status = ""

            if st.button(f"{lb['short']}{status}", key=f"nav_{lid}", use_container_width=True):
                st.session_state.page = "lobster"
                st.session_state.active_lobster = lid
                st.rerun()

        st.divider()

        # 汇总按钮（有任何报告就可看）
        if st.session_state.reports:
            if st.button(t("view_summary"), use_container_width=True):
                st.session_state.page = "summary"
                st.rerun()

        if st.button(t("new_analysis"), use_container_width=True):
            if st.session_state.reports:
                save_to_history()
            for key in list(DEFAULTS.keys()):
                if key == "lang":
                    continue
                st.session_state[key] = DEFAULTS[key] if not isinstance(DEFAULTS[key], (dict, list)) else type(DEFAULTS[key])()
            st.session_state.page = "input"
            st.rerun()
    else:
        st.info(t("input_idea"))

    # 历史记录
    st.divider()
    st.subheader(t("history"))
    history = list_history()
    if not history:
        st.caption(t("no_history"))
    else:
        for i, h in enumerate(history):
            saved = h["saved_at"][:16].replace("T", " ") if h["saved_at"] else ""
            label = f"**{h['anchor_name']}** {h['num_reports']}/5 · {saved}"
            col_load, col_del = st.columns([4, 1])
            with col_load:
                if st.button(label, key=f"hist_{i}", use_container_width=True):
                    data = load_history(h["filename"])
                    if data:
                        restore_session(data)
                        st.rerun()
            with col_del:
                if st.button("x", key=f"del_{i}"):
                    (HISTORY_DIR / h["filename"]).unlink(missing_ok=True)
                    st.rerun()

    st.divider()
    st.caption(t("cost_hint"))


# ══════════════════════════════════════════════════════
# Page: Input Idea
# ══════════════════════════════════════════════════════
if st.session_state.page == "input":
    st.title(t("app_title"))
    st.markdown(t("app_subtitle"))
    st.divider()

    idea = st.text_area(t("input_idea"), value=st.session_state.idea,
                        placeholder=t("input_placeholder"), height=160)

    with st.expander(t("examples_title")):
        for ex in get_examples():
            if st.button(ex, key=f"ex_{hash(ex)}", use_container_width=True):
                st.session_state.idea = ex
                st.rerun()

    if st.button(t("start_analysis"), type="primary", disabled=not idea.strip()):
        st.session_state.idea = idea.strip()
        with st.spinner(t("generating_anchor")):
            st.session_state.anchor = generate_anchor(idea.strip())
        st.session_state.page = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════
# Page: Dashboard — 模式选择 + 龙虾总览
# ══════════════════════════════════════════════════════
elif st.session_state.page == "dashboard":
    st.title(t("app_title"))

    with st.expander(t("anchor"), expanded=False):
        st.json(st.session_state.anchor)

    # ── 模式切换 ──
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if st.button(
            t("mode_sequential"),
            type="primary" if st.session_state.mode == "sequential" else "secondary",
            use_container_width=True,
        ):
            st.session_state.mode = "sequential"
            st.rerun()
        st.caption(t("mode_seq_desc"))
    with mode_col2:
        if st.button(
            t("mode_free"),
            type="primary" if st.session_state.mode == "free" else "secondary",
            use_container_width=True,
        ):
            st.session_state.mode = "free"
            st.rerun()
        st.caption(t("mode_free_desc"))

    st.divider()
    lobsters = get_lobsters()

    if st.session_state.mode == "sequential":
        # ── 顺序模式：显示线性流程，自动进入当前步骤 ──
        seq = st.session_state.seq_step  # 0-4
        for i, lb in enumerate(lobsters):
            lid = lb["id"]
            col_status, col_name, col_action = st.columns([1, 3, 2])
            with col_status:
                if lid in st.session_state.confirmed:
                    st.success(f"{t('step_progress')} {i+1}/5")
                elif lid in st.session_state.reports:
                    st.warning(f"{t('step_progress')} {i+1}/5")
                elif i == seq:
                    st.info(f"{t('step_progress')} {i+1}/5 ▶")
                else:
                    st.caption(f"{t('step_progress')} {i+1}/5")
            with col_name:
                st.markdown(f"**{lb['name']}**")
                st.caption(lb["desc"])
            with col_action:
                if lid in st.session_state.confirmed:
                    # 已确认，可以点击回看
                    if st.button(t("confirmed"), key=f"seq_view_{lid}", use_container_width=True):
                        st.session_state.page = "lobster"
                        st.session_state.active_lobster = lid
                        st.rerun()
                elif lid in st.session_state.reports:
                    # 已生成但未确认
                    if st.button(t("completed"), key=f"seq_review_{lid}", use_container_width=True):
                        st.session_state.page = "lobster"
                        st.session_state.active_lobster = lid
                        st.rerun()
                elif i == seq:
                    # 当前步骤
                    if st.button(t("run_analysis"), key=f"seq_run_{lid}", type="primary", use_container_width=True):
                        st.session_state.page = "lobster"
                        st.session_state.active_lobster = lid
                        st.rerun()
                else:
                    st.caption("—")

    else:
        # ── 自由模式：卡片布局 ──
        cols = st.columns(len(lobsters))
        for i, lb in enumerate(lobsters):
            lid = lb["id"]
            with cols[i]:
                if lid in st.session_state.confirmed:
                    st.success(t("confirmed"))
                elif lid in st.session_state.reports:
                    st.warning(t("completed"))
                else:
                    st.info(t("not_started"))

                st.markdown(f"**{lb['short']}**")
                st.caption(lb["desc"])

                if st.button(lb["name"], key=f"card_{lid}", use_container_width=True):
                    st.session_state.page = "lobster"
                    st.session_state.active_lobster = lid
                    st.rerun()

    # 汇总按钮
    if st.session_state.reports:
        st.divider()
        num_done = len(st.session_state.reports)
        num_confirmed = len(st.session_state.confirmed)
        st.markdown(f"**{num_done}/5** {t('completed')}  |  **{num_confirmed}/5** {t('confirmed')}")
        if st.button(t("view_summary"), type="primary", use_container_width=False):
            st.session_state.page = "summary"
            st.rerun()


# ══════════════════════════════════════════════════════
# Page: Lobster — 单只龙虾分析页
# ══════════════════════════════════════════════════════
elif st.session_state.page == "lobster":
    lobsters = get_lobsters()
    lid = st.session_state.active_lobster
    lb = next((l for l in lobsters if l["id"] == lid), lobsters[0])
    lobster_num = int(lid[1])  # "L3" -> 3

    st.title(lb["name"])
    st.caption(lb["desc"])

    # 返回总览
    if st.button(t("back_to_dashboard")):
        st.session_state.page = "dashboard"
        st.rerun()

    with st.expander(t("anchor"), expanded=False):
        st.json(st.session_state.anchor)

    # 显示已有哪些前序报告可引用
    available_prev = {k: v for k, v in st.session_state.reports.items() if k != lid}
    if available_prev:
        names = [next((l["short"] for l in lobsters if l["id"] == k), k) for k in available_prev]
        st.caption(f"{t('prev_reports_hint')}: {', '.join(names)}")

    st.divider()

    # ── 生成报告 ──
    if lid not in st.session_state.reports:
        # 顺序模式显示当前步骤提示
        if st.session_state.mode == "sequential":
            st.markdown(f"**{t('step_progress')} {lobster_num}/5**")
        if st.button(t("run_analysis"), type="primary"):
            with st.spinner(f"{lb['name']} {t('analyzing')}"):
                prev = {k: v for k, v in st.session_state.reports.items()
                        if k in st.session_state.confirmed and k != lid}
                report = run_lobster(lobster_num, st.session_state.idea, st.session_state.anchor, prev)
                st.session_state.reports[lid] = report
                st.session_state.chat_histories[lid] = []
                st.session_state.supplement_histories[lid] = []
            st.rerun()
    else:
        report = st.session_state.reports[lid]

        # ── 三个 Tab ──
        tab_report, tab_ask, tab_supplement = st.tabs([t("tab_report"), t("tab_ask"), t("tab_supplement")])

        # ────── Tab 1: 报告 ──────
        with tab_report:
            st.markdown(report)

            is_sequential = st.session_state.mode == "sequential"

            if lid not in st.session_state.confirmed:
                if is_sequential:
                    col1, col2, col3 = st.columns(3)
                    if col1.button(t("confirm_report") + " + " + t("next_step"), type="primary"):
                        st.session_state.confirmed[lid] = True
                        # 推进顺序步骤
                        if st.session_state.seq_step < 4:
                            st.session_state.seq_step += 1
                            next_lid = f"L{st.session_state.seq_step + 1}"
                            st.session_state.active_lobster = next_lid
                        else:
                            st.session_state.page = "summary"
                        st.rerun()
                    if col2.button(t("regenerate")):
                        del st.session_state.reports[lid]
                        st.session_state.chat_histories[lid] = []
                        st.session_state.supplement_histories[lid] = []
                        st.rerun()
                    if col3.button(t("skip_step")):
                        # 跳过不确认，直接进下一步
                        if st.session_state.seq_step < 4:
                            st.session_state.seq_step += 1
                            next_lid = f"L{st.session_state.seq_step + 1}"
                            st.session_state.active_lobster = next_lid
                        else:
                            st.session_state.page = "summary"
                        st.rerun()
                else:
                    col1, col2 = st.columns(2)
                    if col1.button(t("confirm_report"), type="primary"):
                        st.session_state.confirmed[lid] = True
                        st.rerun()
                    if col2.button(t("regenerate")):
                        del st.session_state.reports[lid]
                        st.session_state.chat_histories[lid] = []
                        st.session_state.supplement_histories[lid] = []
                        st.rerun()
            else:
                st.success(t("confirmed"))
                if is_sequential:
                    if st.button(t("next_step")):
                        if st.session_state.seq_step < 4:
                            st.session_state.seq_step += 1
                            next_lid = f"L{st.session_state.seq_step + 1}"
                            st.session_state.active_lobster = next_lid
                        else:
                            st.session_state.page = "summary"
                        st.rerun()

            # 下载
            st.divider()
            anchor_name = st.session_state.anchor.get("name", "product")
            dl1, dl2 = st.columns(2)
            dl1.download_button(
                t("download_md"),
                data=f"# {lb['name']}\n\n**{anchor_name}**\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n{report}",
                file_name=f"{lid}_{lb['short']}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown", use_container_width=True,
            )
            dl2.download_button(
                t("download_json"),
                data=json.dumps({"lobster": lb, "idea": st.session_state.idea, "anchor": st.session_state.anchor,
                                 "report": report, "chat_history": st.session_state.chat_histories.get(lid, []),
                                 "supplements": st.session_state.supplement_histories.get(lid, []),
                                 "generated_at": datetime.now().isoformat()}, ensure_ascii=False, indent=2),
                file_name=f"{lid}_{lb['short']}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json", use_container_width=True,
            )

        # ────── Tab 2: 询问细节 ──────
        with tab_ask:
            st.markdown(t("ask_placeholder"))
            st.divider()

            chat_history = st.session_state.chat_histories.get(lid, [])
            for msg in chat_history:
                avatar = "👤" if msg["role"] == "user" else "🦞"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

            user_input = st.chat_input(t("ask_placeholder"), key=f"ask_{lid}")
            if user_input:
                chat_history.append({"role": "user", "content": user_input})
                st.session_state.chat_histories[lid] = chat_history
                with st.spinner(t("thinking")):
                    reply = chat_with_lobster(
                        lobster_num, report, chat_history[:-1],
                        user_input, st.session_state.idea, st.session_state.anchor,
                    )
                chat_history.append({"role": "assistant", "content": reply})
                st.session_state.chat_histories[lid] = chat_history
                st.rerun()

        # ────── Tab 3: 补充信息 ──────
        with tab_supplement:
            supplement_history = st.session_state.supplement_histories.get(lid, [])

            # 显示补充历史
            if supplement_history:
                for sh in supplement_history:
                    with st.expander(f"{sh['time']} — {sh['content'][:40]}..."):
                        st.markdown(f"**补充内容：** {sh['content']}")

            supplement_text = st.text_area(
                t("supplement_placeholder"),
                key=f"supp_input_{lid}",
                height=120,
                placeholder=t("supplement_placeholder"),
            )

            if supplement_text and st.button(t("supplement_update"), type="primary"):
                with st.spinner(t("updating_report")):
                    prev = {k: v for k, v in st.session_state.reports.items()
                            if k in st.session_state.confirmed and k != lid}
                    new_report = supplement_report(
                        lobster_num, report, supplement_text,
                        st.session_state.idea, st.session_state.anchor, prev,
                    )
                    st.session_state.reports[lid] = new_report
                    # 记录补充历史
                    supplement_history.append({
                        "time": datetime.now().strftime("%H:%M"),
                        "content": supplement_text,
                    })
                    st.session_state.supplement_histories[lid] = supplement_history
                    # 如果已确认，补充后取消确认
                    if lid in st.session_state.confirmed:
                        del st.session_state.confirmed[lid]
                st.rerun()


# ══════════════════════════════════════════════════════
# Page: Summary — 汇总报告
# ══════════════════════════════════════════════════════
elif st.session_state.page == "summary":
    st.title(t("summary_title"))

    if st.button(t("back_to_dashboard")):
        st.session_state.page = "dashboard"
        st.rerun()

    # 自动保存
    if len(st.session_state.confirmed) == 5 and "auto_saved" not in st.session_state:
        save_to_history()
        st.session_state.auto_saved = True

    lobsters = get_lobsters()
    anchor_text = st.session_state.anchor.get("product_anchor", st.session_state.idea)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 状态总览
    for lb in lobsters:
        lid = lb["id"]
        if lid in st.session_state.confirmed:
            st.success(f"{lb['short']} — {t('confirmed')}")
        elif lid in st.session_state.reports:
            st.warning(f"{lb['short']} — {t('completed')}")
        else:
            st.error(f"{lb['short']} — {t('not_started')}")

    st.divider()

    # 报告内容
    sections = {"L1": "1", "L2": "2", "L3": "3", "L4": "4", "L5": "5"}
    full_report = f"# {t('summary_title')}\n\n**{anchor_text}**\n**{st.session_state.idea}**\n**{now}**\n\n---\n\n"
    for lb in lobsters:
        lid = lb["id"]
        content = st.session_state.reports.get(lid, f"[{t('not_started')}]")
        full_report += f"## {sections[lid]}. {lb['name']}\n\n{content}\n\n---\n\n"

    st.markdown(full_report)
    st.divider()

    col1, col2 = st.columns(2)
    col1.download_button(
        t("download_md"), data=full_report,
        file_name=f"lobster_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown", use_container_width=True,
    )
    export_data = {
        "idea": st.session_state.idea, "anchor": st.session_state.anchor,
        "reports": st.session_state.reports, "chat_histories": st.session_state.chat_histories,
        "supplement_histories": st.session_state.supplement_histories, "generated_at": now,
    }
    col2.download_button(
        t("download_json"),
        data=json.dumps(export_data, ensure_ascii=False, indent=2),
        file_name=f"lobster_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json", use_container_width=True,
    )

    st.divider()

    # 最终对话
    st.subheader(t("summary_discuss"))
    st.markdown(t("summary_discuss_hint"))

    for msg in st.session_state.final_chat:
        avatar = "👤" if msg["role"] == "user" else "🦞"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    final_input = st.chat_input(t("summary_input"))
    if final_input:
        st.session_state.final_chat.append({"role": "user", "content": final_input})
        sys_prompt = f"""你是呆瓜军团的总指挥，拥有 5 只呆瓜的全部分析能力。
产品 Idea：{st.session_state.idea}
产品锚点：{json.dumps(st.session_state.anchor, ensure_ascii=False)}

各呆瓜报告摘要：
""" + "\n".join([f"- {lb['short']}：{st.session_state.reports.get(lb['id'], '未完成')[:1500]}" for lb in lobsters]) + "\n\n请基于完整上下文回答。"

        messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.final_chat]
        with st.spinner(t("thinking")):
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=3000,
                system=sys_prompt, messages=messages,
            )
            reply = resp.content[0].text
        st.session_state.final_chat.append({"role": "assistant", "content": reply})
        st.rerun()
