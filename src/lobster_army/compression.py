"""
龙虾军团 — 压缩摘要模块
用 Haiku 将龙虾完整输出压缩为结构化 JSON，供下游龙虾读取。
包含 Schema 校验、重试、规则 Fallback 三层防护。
"""

import json
import re
from typing import Dict, Any, Optional
from anthropic import Anthropic
from jsonschema import validate, ValidationError
from pathlib import Path
from dotenv import load_dotenv

PKG_DIR = Path(__file__).parent
load_dotenv(PKG_DIR.parent.parent / ".env")
load_dotenv()

client = Anthropic()

COMPRESS_PROMPT = """你是一个信息压缩专家。将以下产品分析报告压缩为严格的 JSON 格式。
只保留核心结论和关键数字，丢弃所有推理过程。

要求：
1. 严格遵循下方 JSON 结构，不要添加任何字段
2. 所有数字必须保留原始来源和年份标注
3. 不要修改 product_anchor 字段的内容
4. 如果原文缺少某个字段的数据，填写 "N/A"
5. 只输出 JSON，不要有任何其他文字

目标 JSON 结构：
{schema_hint}

原始报告：
{content}
"""


def load_schema(schema_name: str) -> dict:
    """加载 JSON Schema 文件"""
    schema_path = PKG_DIR / "schemas" / f"{schema_name}.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text(encoding="utf-8"))
    return {}


def compress_with_haiku(
    content: str,
    anchor: Dict[str, Any],
    schema_name: str = "summary_l1",
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    用 Haiku 压缩单只龙虾的输出为结构化 JSON。

    Args:
        content: 龙虾的完整输出文本
        anchor: 产品锚点（不经过 Haiku，由 Orchestrator 直接注入）
        schema_name: 对应的 JSON Schema 名称
        max_tokens: 输出 token 上限

    Returns:
        压缩后的结构化 JSON dict
    """
    schema = load_schema(schema_name)
    schema_hint = json.dumps(schema.get("properties", {}), ensure_ascii=False, indent=2)

    prompt = COMPRESS_PROMPT.format(schema_hint=schema_hint, content=content)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()

    # 提取 JSON（处理 Haiku 可能包裹在 ```json ... ``` 中的情况）
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if not json_match:
        raise ValueError(f"Haiku 返回内容中未找到 JSON: {raw_text[:200]}")

    result = json.loads(json_match.group())

    # 强制注入 anchor（不信任 Haiku 的 anchor 输出）
    result["product_anchor"] = anchor.get(
        "product_anchor",
        f"为{anchor.get('target_user', '?')}在{anchor.get('scenario', '?')}下解决{anchor.get('core_problem', '?')}"
    )

    # Schema 校验
    if schema:
        validate(instance=result, schema=schema)

    cost = (response.usage.input_tokens * 1.0 + response.usage.output_tokens * 5.0) / 1_000_000
    return result, cost


def fallback_extract(content: str, anchor: Dict[str, Any]) -> Dict[str, Any]:
    """
    规则 Fallback：当 Haiku 压缩失败时，用正则从原始输出中提取关键数据。
    质量下降 ~30%，但保证链路不断。
    """
    result = {
        "product_anchor": anchor.get(
            "product_anchor",
            f"为{anchor.get('target_user', '?')}在{anchor.get('scenario', '?')}下解决{anchor.get('core_problem', '?')}"
        ),
    }

    # 尝试提取 TAM/SAM/SOM
    tam_match = re.search(r'TAM[：:]\s*\$?([\d,.]+\s*[BMK]?)', content, re.IGNORECASE)
    sam_match = re.search(r'SAM[：:]\s*\$?([\d,.]+\s*[BMK]?)', content, re.IGNORECASE)
    som_match = re.search(r'SOM[：:]\s*\$?([\d,.]+\s*[BMK]?)', content, re.IGNORECASE)

    result["market"] = {
        "tam": tam_match.group(1) if tam_match else "N/A [fallback]",
        "sam": sam_match.group(1) if sam_match else "N/A [fallback]",
        "som": som_match.group(1) if som_match else "N/A [fallback]",
        "source_year": "N/A [fallback extraction]",
    }

    # 提取用户相关信息
    result["target_users"] = [{"persona": anchor.get("target_user", "N/A"), "willingness_to_pay": "N/A [fallback]"}]
    result["competitors"] = []
    result["key_opportunity"] = "N/A [fallback extraction - 需人工补充]"

    return result


def compress_with_fallback(
    content: str,
    anchor: Dict[str, Any],
    schema_name: str = "summary_l1",
) -> tuple[Dict[str, Any], float]:
    """
    三层防护的压缩流程：
    1. Haiku 压缩 + Schema 校验
    2. 失败 → 重试一次
    3. 再失败 → 规则 Fallback
    """
    total_cost = 0.0

    # 第一次尝试
    try:
        result, cost = compress_with_haiku(content, anchor, schema_name)
        total_cost += cost
        return result, total_cost
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        print(f"  ⚠️ 压缩首次失败: {e}")

    # 重试一次
    try:
        result, cost = compress_with_haiku(content, anchor, schema_name)
        total_cost += cost
        return result, total_cost
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        print(f"  ⚠️ 压缩重试失败: {e}")

    # Fallback：规则提取
    print("  ⚠️ 降级为规则 Fallback 提取")
    result = fallback_extract(content, anchor)
    return result, total_cost


def merge_and_validate(
    summary_l1: Dict[str, Any],
    summary_l2: Dict[str, Any],
    anchor: Dict[str, Any],
) -> Dict[str, Any]:
    """
    合并龙虾一+二的摘要为 combined_summary.json。
    anchor 由 Orchestrator 直接注入，不经过合并逻辑。
    """
    combined = {
        "product_anchor": anchor.get(
            "product_anchor",
            f"为{anchor.get('target_user', '?')}在{anchor.get('scenario', '?')}下解决{anchor.get('core_problem', '?')}"
        ),
        "market": summary_l1.get("market", {}),
        "target_users": summary_l1.get("target_users", []),
        "competitors": summary_l2.get("competitors", []),
        "key_opportunity": summary_l2.get("key_opportunity", ""),
    }

    # 保存合并摘要
    return combined
