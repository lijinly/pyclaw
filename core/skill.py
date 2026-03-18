"""
Skills 技能基类与注册器
每个 Skill 是一个可异步调用的独立能力单元。
"""
import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class Skill(ABC):
    """技能基类"""

    # 子类必须声明名称和描述，供 LLM 做工具选择
    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行技能，返回结果"""
        ...

    def schema(self) -> dict:
        """返回技能的简单描述 schema，可扩展为 function-calling 格式"""
        sig = inspect.signature(self.execute)
        params = {
            k: str(v.annotation)
            for k, v in sig.parameters.items()
            if k != "self"
        }
        return {
            "name": self.name,
            "description": self.description,
            "parameters": params,
        }


class SkillRegistry:
    """技能注册中心 —— 管理所有已注册技能"""

    def __init__(self):
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """注册一个技能实例"""
        if not skill.name:
            raise ValueError(f"Skill {type(skill).__name__} must have a name")
        self._skills[skill.name] = skill
        print(f"  [Registry] ✓ 技能已注册: {skill.name}")

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> list[dict]:
        return [s.schema() for s in self._skills.values()]

    async def run(self, name: str, **kwargs) -> Any:
        skill = self.get(name)
        if skill is None:
            raise KeyError(f"未找到技能: {name}")
        return await skill.execute(**kwargs)
