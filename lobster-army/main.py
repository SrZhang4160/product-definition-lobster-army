#!/usr/bin/env python3
"""
龙虾军团 — 入口脚本
用法：
    python main.py "你的产品 Idea"          # 新运行
    python main.py --resume <run_id>        # 断点续跑
    python main.py --list                   # 列出历史运行
"""

import argparse
import sys
from pathlib import Path

from flow import LobsterArmyFlow
from state import RunState


RUNS_DIR = "runs"


def new_run(idea: str) -> None:
    """启动一次全新运行"""
    print("=" * 60)
    print("🦞 龙虾军团 — 产品分析系统")
    print("=" * 60)
    print(f"\n📝 Idea: {idea[:120]}{'...' if len(idea) > 120 else ''}\n")

    flow = LobsterArmyFlow()
    result = flow.kickoff(inputs={"idea": idea})

    state: RunState = flow.state
    print("\n" + "=" * 60)
    print("✅ 运行完成！")
    print(f"   Run ID  : {state.run_id}")
    print(f"   Phase   : {state.phase}")
    print(f"   总成本   : ${state.total_cost:.4f}")

    # 找到输出文件
    run_path = Path(RUNS_DIR) / state.run_id
    report = run_path / "final_report.md"
    if report.exists():
        print(f"   报告路径 : {report}")
    else:
        partial = run_path / "partial_report.md"
        if partial.exists():
            print(f"   部分报告 : {partial}")

    if state.errors:
        print(f"\n⚠️  运行过程中有 {len(state.errors)} 个错误:")
        for err in state.errors[-5:]:
            print(f"   • {err}")


def resume_run(run_id: str) -> None:
    """从断点恢复运行（当前版本：重新运行未完成的阶段）"""
    try:
        state = RunState.load(run_id, RUNS_DIR)
    except FileNotFoundError:
        print(f"❌ 找不到运行记录: {run_id}")
        print(f"   请检查 {RUNS_DIR}/ 目录")
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

    # 当前版本：从头重跑（保留 anchor 如果已有）
    # TODO: 未来版本实现真正的断点续跑（跳过已完成步骤）
    print(f"\n⚠️  当前版本将从头重新运行（已有 anchor 会被复用）")
    print(f"   原始 Idea: {state.idea[:120]}\n")

    flow = LobsterArmyFlow()
    result = flow.kickoff(inputs={"idea": state.idea})

    new_state: RunState = flow.state
    print("\n" + "=" * 60)
    print("✅ 续跑完成！")
    print(f"   Run ID  : {new_state.run_id}")
    print(f"   总成本   : ${new_state.total_cost:.4f}")


def list_runs() -> None:
    """列出所有历史运行"""
    runs_path = Path(RUNS_DIR)
    if not runs_path.exists():
        print("📂 还没有任何运行记录。")
        return

    runs = sorted(runs_path.iterdir(), reverse=True)
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
            state = RunState.load(run_dir.name, RUNS_DIR)
            status = "✅" if state.phase == "done" else "⏸️" if state.phase == "partial" else "❌"
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
示例:
  python main.py "一个帮助程序员管理代码片段的工具"
  python main.py --resume 20260330_143022
  python main.py --list
        """,
    )

    parser.add_argument("idea", nargs="?", help="产品 Idea（一句话描述）")
    parser.add_argument("--resume", metavar="RUN_ID", help="从断点续跑指定的 run_id")
    parser.add_argument("--list", action="store_true", help="列出所有历史运行")

    args = parser.parse_args()

    if args.list:
        list_runs()
    elif args.resume:
        resume_run(args.resume)
    elif args.idea:
        new_run(args.idea)
    else:
        parser.print_help()
        print("\n💡 提示：请提供一个产品 Idea，例如:")
        print('   python main.py "一个帮助远程团队异步协作的工具"')


if __name__ == "__main__":
    main()
