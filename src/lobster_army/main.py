#!/usr/bin/env python3
"""
龙虾军团 — CrewAI AMP 入口
AMP Entry Point: kickoff() / plot()
"""

import sys
import argparse
from pathlib import Path

from .flow import LobsterArmyFlow
from .state import RunState


RUNS_DIR = Path(__file__).parent / "runs"


# ══════════════════════════════════════════════════════
# AMP Entry Points (required by CrewAI AMP)
# ══════════════════════════════════════════════════════

def kickoff(inputs: dict | None = None):
    """
    CrewAI AMP entry point.
    Called by AMP runtime to start the flow.

    Args:
        inputs: dict with at least {"idea": "..."} key
    """
    if inputs is None:
        inputs = {}

    idea = inputs.get("idea", "")
    if not idea:
        raise ValueError("Missing required input: 'idea'. Provide a product idea string.")

    print("=" * 60)
    print("🦞 龙虾军团 — 产品分析系统 (Lobster Army)")
    print("=" * 60)
    print(f"\n📝 Idea: {idea[:120]}{'...' if len(idea) > 120 else ''}\n")

    flow = LobsterArmyFlow()
    result = flow.kickoff(inputs={"idea": idea})

    state: RunState = flow.state
    print("\n" + "=" * 60)
    print("✅ 运行完成！ (Run Complete)")
    print(f"   Run ID  : {state.run_id}")
    print(f"   Phase   : {state.phase}")
    print(f"   Cost    : ${state.total_cost:.4f}")

    run_path = RUNS_DIR / state.run_id
    report = run_path / "final_report.md"
    if report.exists():
        print(f"   Report  : {report}")

    if state.errors:
        print(f"\n⚠️  Errors ({len(state.errors)}):")
        for err in state.errors[-5:]:
            print(f"   • {err}")

    return result


def plot():
    """
    Generate and display the flow visualization.
    Called by `crewai flow plot` command.
    """
    flow = LobsterArmyFlow()
    flow.plot()


# ══════════════════════════════════════════════════════
# CLI Interface (for local development)
# ══════════════════════════════════════════════════════

def resume_run(run_id: str) -> None:
    """从断点恢复运行"""
    try:
        state = RunState.load(run_id, str(RUNS_DIR))
    except FileNotFoundError:
        print(f"❌ 找不到运行记录: {run_id}")
        sys.exit(1)

    print("=" * 60)
    print("🦞 龙虾军团 — 断点续跑")
    print("=" * 60)
    print(f"\n   Run ID  : {state.run_id}")
    print(f"   Phase   : {state.phase}")
    print(f"   Idea    : {state.idea[:80]}...")

    if state.phase == "done":
        print("\n✅ 该运行已完成，无需续跑。")
        return

    print(f"\n⚠️  当前版本将从头重新运行（已有 anchor 会被复用）")
    kickoff(inputs={"idea": state.idea})


def list_runs() -> None:
    """列出所有历史运行"""
    if not RUNS_DIR.exists():
        print("📂 还没有任何运行记录。")
        return

    runs = sorted(RUNS_DIR.iterdir(), reverse=True)
    if not runs:
        print("📂 还没有任何运行记录。")
        return

    print("=" * 60)
    print("🦞 龙虾军团 — 历史运行")
    print("=" * 60)

    for run_dir in runs:
        if not run_dir.is_dir():
            continue
        state_file = run_dir / "state.json"
        if not state_file.exists():
            continue
        try:
            state = RunState.load(run_dir.name, str(RUNS_DIR))
            status = "✅" if state.phase == "done" else "⏸️"
            print(f"\n  {status} {run_dir.name}")
            print(f"     Phase: {state.phase} | Cost: ${state.total_cost:.4f}")
            print(f"     Idea:  {state.idea[:80]}{'...' if len(state.idea) > 80 else ''}")
        except Exception:
            print(f"\n  ⚠️  {run_dir.name} (状态文件损坏)")


def main():
    parser = argparse.ArgumentParser(
        description="🦞 龙虾军团 — 产品分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m lobster_army "一个帮助程序员管理代码片段的工具"
  python -m lobster_army --resume 20260330_143022
  python -m lobster_army --list
        """,
    )
    parser.add_argument("idea", nargs="?", help="产品 Idea")
    parser.add_argument("--resume", metavar="RUN_ID", help="从断点续跑")
    parser.add_argument("--list", action="store_true", help="列出历史运行")

    args = parser.parse_args()

    if args.list:
        list_runs()
    elif args.resume:
        resume_run(args.resume)
    elif args.idea:
        kickoff(inputs={"idea": args.idea})
    else:
        parser.print_help()
        print("\n💡 提示：请提供一个产品 Idea，例如:")
        print('   python -m lobster_army "一个帮助远程团队异步协作的工具"')


if __name__ == "__main__":
    main()
