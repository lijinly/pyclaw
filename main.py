"""
pyClaw Agent —— 主入口
运行方式：
    python main.py                  # 交互式 CLI
    python main.py --demo           # 运行内置演示
"""
import argparse
import asyncio
import os
import sys


def _setup_path():
    """将项目根目录加入 sys.path"""
    root = os.path.dirname(os.path.abspath(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)


_setup_path()

from core.agent import Agent
from core.llm import LLMConfig
from core.skill import SkillRegistry
from skills.builtin import CalculatorSkill, DateTimeSkill, EchoSkill, WebSearchSkill


# ─── 初始化 ───────────────────────────────────────────────────────────────────

def build_agent() -> Agent:
    """构建并返回一个已注册所有内置技能的 Agent 实例"""
    # 1. LLM 配置 —— 从环境变量读取，也可在此直接填写
    config = LLMConfig(
        api_key=os.getenv("DASHSCOPE_API_KEY", "your-dashscope-api-key-here"),
        base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
    )

    # 2. 注册技能
    registry = SkillRegistry()
    for skill in [CalculatorSkill(), DateTimeSkill(), EchoSkill(), WebSearchSkill()]:
        registry.register(skill)

    # 3. 创建 Agent
    return Agent(llm_config=config, registry=registry)


# ─── 演示模式 ─────────────────────────────────────────────────────────────────

async def run_demo(agent: Agent) -> None:
    demo_inputs = [
        "现在是几点？今天是星期几？",
        "帮我计算 sin(pi/6) + sqrt(144) 的结果",
        "echo 一下这段文字：pyClaw Agent 启动成功！",
        "Python 是什么？",
    ]

    print("\n" + "=" * 60)
    print("  pyClaw Agent — Demo 模式")
    print("=" * 60)

    for q in demo_inputs:
        print(f"\n👤 用户: {q}")
        try:
            answer = await agent.run(q)
            print(f"🤖 Agent: {answer}")
        except Exception as e:
            print(f"⚠️  错误: {e}")
        print("-" * 60)


# ─── 交互式 CLI ───────────────────────────────────────────────────────────────

async def run_cli(agent: Agent) -> None:
    print("\n" + "=" * 60)
    print("  pyClaw Agent — 交互模式  (输入 'exit' 退出 | 'reset' 清空历史)")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("👤 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("再见！")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("✓ 对话历史已清空\n")
            continue

        try:
            reply = await agent.run(user_input)
            print(f"🤖 Agent: {reply}\n")
        except Exception as e:
            print(f"⚠️  出错了: {e}\n")


# ─── 入口 ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(description="pyClaw Agent")
    parser.add_argument("--demo", action="store_true", help="运行内置演示（无需 LLM）")
    args = parser.parse_args()

    print("🚀 正在初始化 pyClaw Agent ...")
    agent = build_agent()
    print("✓ Agent 就绪！\n")

    if args.demo:
        await run_demo(agent)
    else:
        await run_cli(agent)


if __name__ == "__main__":
    asyncio.run(main())
