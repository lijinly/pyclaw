"""
智能体核心 —— Agent
运行循环：感知输入 → LLM 决策 → 技能调用 → 结果回填 → 输出
"""
import asyncio
import json
import re
from typing import Optional

from core.llm import LLMClient, LLMConfig
from core.skill import SkillRegistry


# ─── 系统提示词 ────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT_TEMPLATE = """你是一个智能助手，名叫 pyClaw Agent。

你拥有以下技能工具，当用户的问题需要借助工具时，请严格按照下面格式输出调用指令，不要输出任何其他内容：
<tool_call>
{{"name": "技能名称", "args": {{"参数名": "参数值"}}}}
</tool_call>

可用技能列表：
{skills_json}

规则：
1. 如果问题可以直接回答，就直接回答，不要调用工具。
2. 如果需要工具，只输出一个 <tool_call> 块。
3. 收到工具结果后，用自然语言给出最终回答。
4. 保持回答简洁、友好、准确。
"""


class Agent:
    """
    极简 ReAct 风格智能体。
    
    工作流程（单轮）：
      用户输入
        → LLM 判断是否需要调用技能
        → 若需要：执行技能 → 将结果注入上下文 → LLM 生成最终回复
        → 若不需要：直接返回 LLM 回复
    """

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        registry: Optional[SkillRegistry] = None,
        max_tool_rounds: int = 3,
    ):
        self.llm = LLMClient(llm_config or LLMConfig())
        self.registry = registry or SkillRegistry()
        self.max_tool_rounds = max_tool_rounds
        self.history: list[dict] = []  # 多轮对话历史

    # ── 公开接口 ──────────────────────────────────────────────────────────────

    async def run(self, user_input: str) -> str:
        """处理一条用户消息，返回 Agent 回复"""
        self.history.append({"role": "user", "content": user_input})
        reply = await self._think_and_act()
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        """清空对话历史"""
        self.history.clear()

    # ── 内部逻辑 ──────────────────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        skills = self.registry.list_skills()
        return _SYSTEM_PROMPT_TEMPLATE.format(
            skills_json=json.dumps(skills, ensure_ascii=False, indent=2)
        )

    async def _think_and_act(self) -> str:
        """
        ReAct 循环：最多执行 max_tool_rounds 轮工具调用。
        每轮：LLM 输出 → 解析是否有 tool_call → 执行 → 结果注入。
        """
        working_history = list(self.history)  # 本轮工作副本

        for round_idx in range(self.max_tool_rounds + 1):
            llm_reply = await self.llm.chat(
                messages=working_history,
                system_prompt=self._system_prompt(),
            )

            tool_call = self._parse_tool_call(llm_reply)
            if tool_call is None:
                # 没有工具调用 → 直接返回
                return llm_reply.strip()

            if round_idx >= self.max_tool_rounds:
                # 超出最大轮次，强制返回当前回复
                return llm_reply.strip()

            # 执行工具
            tool_result = await self._execute_tool(tool_call)

            # 将工具调用 + 结果追加到工作历史，让 LLM 继续推理
            working_history.append({"role": "assistant", "content": llm_reply})
            working_history.append({
                "role": "user",
                "content": f"[工具 '{tool_call['name']}' 执行结果]\n{json.dumps(tool_result, ensure_ascii=False, indent=2)}\n\n请根据以上结果，用自然语言给出最终回答。",
            })

        return "抱歉，处理您的请求时遇到了问题，请稍后再试。"

    @staticmethod
    def _parse_tool_call(text: str) -> Optional[dict]:
        """从 LLM 输出中提取 <tool_call> JSON"""
        match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    async def _execute_tool(self, tool_call: dict) -> dict:
        """异步执行工具调用"""
        name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        try:
            result = await self.registry.run(name, **args)
            return {"status": "ok", "data": result}
        except KeyError as e:
            return {"status": "error", "error": f"技能不存在: {e}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
