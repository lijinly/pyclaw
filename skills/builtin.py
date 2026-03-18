"""
内置技能集合 —— 展示如何基于 Skill 基类实现具体能力
"""
import asyncio
import datetime
import math
from typing import Any

from core.skill import Skill


class CalculatorSkill(Skill):
    """数学计算技能"""
    name = "calculator"
    description = "执行数学表达式计算，支持加减乘除、幂运算、三角函数等。参数 expr 为合法的 Python 数学表达式字符串。"

    # 安全白名单
    _SAFE_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    _SAFE_NAMES.update({"abs": abs, "round": round, "int": int, "float": float})

    async def execute(self, expr: str) -> Any:
        await asyncio.sleep(0)  # 模拟异步 IO
        try:
            result = eval(expr, {"__builtins__": {}}, self._SAFE_NAMES)  # noqa: S307
            return {"result": result, "expr": expr}
        except Exception as e:
            return {"error": str(e), "expr": expr}


class DateTimeSkill(Skill):
    """时间查询技能"""
    name = "datetime"
    description = "获取当前日期和时间信息。无需参数。"

    async def execute(self) -> Any:
        await asyncio.sleep(0)
        now = datetime.datetime.now()
        return {
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
            "timestamp": int(now.timestamp()),
        }


class EchoSkill(Skill):
    """回声技能 —— 用于调试，将输入原样返回"""
    name = "echo"
    description = "将输入内容原样返回，用于测试技能管道是否正常工作。参数 message 为要回显的字符串。"

    async def execute(self, message: str) -> Any:
        await asyncio.sleep(0)
        return {"echo": message, "length": len(message)}


class WebSearchSkill(Skill):
    """
    网络搜索技能（Stub）
    实际使用时替换为真实搜索 API（如 Bing Search、SerpAPI 等）
    """
    name = "web_search"
    description = "在互联网上搜索信息。参数 query 为搜索关键词字符串。"

    async def execute(self, query: str) -> Any:
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        # TODO: 替换为真实搜索 API 调用
        return {
            "query": query,
            "results": [
                {"title": f"[示例] 关于 '{query}' 的搜索结果 1", "snippet": "这是一个占位搜索结果，请配置真实的搜索 API。"},
                {"title": f"[示例] 关于 '{query}' 的搜索结果 2", "snippet": "替换 WebSearchSkill.execute 中的逻辑即可接入真实数据。"},
            ],
            "note": "当前为 Stub 模式，请在 skills/builtin.py 中配置真实 API",
        }
