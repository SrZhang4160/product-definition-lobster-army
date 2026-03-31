"""
龙虾军团 — 检查点 B：语义一致性校验
在龙虾三输出后、龙虾四运行前执行。
用 Haiku 比对龙虾三的产品定位与原始 Idea 的语义一致性。
"""

import json
import re
from typing import Dict, Any, Tuple
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

PKG_DIR = Path(__file__).parent
load_dotenv(PKG_DIR.parent.parent / ".env")
load_dotenv()

client = Anthropic()

GATE_CHECK_PROMPT = """你是一个语义一致性评审员。

原始产品 Idea：
{idea}

产品锚点：
{anchor}

龙虾三的产品定义输出（摘要）：
{lobster3_excerpt}

请评估：龙虾三的产品定义是否忠实于原始 Idea 和锚点？

评分标准（0-10）：
- 10: 完全一致，产品定义精准回应 Idea 的核心问题
- 7-9: 大方向一致，有些细节偏差但不影响价值
- 4-6: 部分偏离，产品定义涵盖了 Idea 但夹带了不相关的方向
- 1-3: 严重偏离，产品定义与 Idea 解决的问题不匹配
- 0: 完全跑偏

只输出 JSON，不要有任何其他文字：
{{"score": <0-10的整数>, "reason": "<一句话解释>"}}
"""


def check_semantic_consistency(
    anchor: Dict[str, Any],
    idea: str,
    lobster3_content: str,
    max_excerpt_length: int = 500,
) -> Tuple[int, str, float]:
    """
    用 Haiku 做轻量级语义一致性校验。

    Args:
        anchor: 产品锚点 JSON
        idea: 用户原始 Idea 文本
        lobster3_content: 龙虾三的完整输出
        max_excerpt_length: 龙虾三输出截取长度（节省 token）

    Returns:
        (score, reason, cost)
    """
    # 截取龙虾三输出的前 N 字符（通常包含产品定位句和核心定义）
    excerpt = lobster3_content[:max_excerpt_length]
    if len(lobster3_content) > max_excerpt_length:
        excerpt += "\n... [已截断]"

    anchor_str = json.dumps(anchor, ensure_ascii=False, indent=2)

    prompt = GATE_CHECK_PROMPT.format(
        idea=idea,
        anchor=anchor_str,
        lobster3_excerpt=excerpt,
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()

    # 解析 JSON 响应
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if not json_match:
        # 解析失败 → 保守处理，给中间分
        return 5, "Gate check 响应解析失败，保守通过", 0.0

    result = json.loads(json_match.group())
    score = int(result.get("score", 5))
    reason = result.get("reason", "无解释")

    cost = (response.usage.input_tokens * 1.0 + response.usage.output_tokens * 5.0) / 1_000_000

    return score, reason, cost
