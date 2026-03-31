"""
龙虾军团 — 运行状态模型
所有 Flow 步骤共享的状态，支持序列化/反序列化实现断点续跑
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import json


class LobsterOutput(BaseModel):
    """单只龙虾的输出记录"""
    content: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    search_calls: int = 0
    search_failures: int = 0
    model: str = ""
    duration_seconds: float = 0.0


class RunState(BaseModel):
    """
    Flow 的完整运行状态。
    每一步完成后调用 persist() 写入磁盘，崩溃后可从 JSON 恢复。
    """

    # ── 基本信息 ──
    idea: str = ""
    run_id: str = ""
    phase: str = "init"  # init | anchor | parallel | compress | lobster_3 | gate_check | lobster_4 | lobster_5 | assemble | done | partial | failed
    started_at: str = ""

    # ── 锚点 ──
    anchor: Dict[str, Any] = Field(default_factory=dict)

    # ── 各龙虾输出 ──
    L1: Optional[LobsterOutput] = None
    L2: Optional[LobsterOutput] = None
    L3: Optional[LobsterOutput] = None
    L4: Optional[LobsterOutput] = None
    L5: Optional[LobsterOutput] = None

    # ── 压缩摘要 ──
    summary_l1: Dict[str, Any] = Field(default_factory=dict)
    summary_l2: Dict[str, Any] = Field(default_factory=dict)
    combined_summary: Dict[str, Any] = Field(default_factory=dict)

    # ── 检查点 ──
    gate_score: Optional[int] = None
    gate_retries: int = 0

    # ── 元数据 ──
    total_cost: float = 0.0
    errors: List[str] = Field(default_factory=list)
    prompt_version: str = "v1"
    config_hash: str = ""

    def persist(self, runs_dir: str = "runs"):
        """每步完成后调用，写入 /runs/{run_id}/state.json"""
        run_path = Path(runs_dir) / self.run_id
        run_path.mkdir(parents=True, exist_ok=True)
        state_file = run_path / "state.json"
        state_file.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    def save_lobster_output(self, lobster_id: str, output: LobsterOutput, runs_dir: str = "runs"):
        """将单只龙虾的完整输出写入冷存储"""
        run_path = Path(runs_dir) / self.run_id
        run_path.mkdir(parents=True, exist_ok=True)
        output_file = run_path / f"{lobster_id}_output.json"
        output_file.write_text(output.model_dump_json(indent=2), encoding="utf-8")

    def add_cost(self, cost: float):
        """累加成本"""
        self.total_cost += cost

    def add_error(self, error: str):
        """记录错误"""
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")

    @classmethod
    def load(cls, run_id: str, runs_dir: str = "runs") -> "RunState":
        """从磁盘加载已保存的状态（用于断点续跑）"""
        state_file = Path(runs_dir) / run_id / "state.json"
        if not state_file.exists():
            raise FileNotFoundError(f"State file not found: {state_file}")
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return cls(**data)
