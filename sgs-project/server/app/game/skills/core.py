from abc import ABC, abstractmethod
from typing import Optional, Tuple, TYPE_CHECKING

# 使用 TYPE_CHECKING 避免运行时循环引用
if TYPE_CHECKING:
    from app.game.room import GameRoom
    from app.game.player import PlayerState
    from app.game.card import Card

class CardSkill(ABC):
    """
    所有卡牌技能的基类 (策略模式接口)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """技能/卡牌名称，用于注册表查找"""
        pass

    def validate(self, room: 'GameRoom', player: 'PlayerState', card: 'Card', target_sid: Optional[str]) -> Tuple[bool, str]:
        """
        校验当前是否可以使用此牌
        :return: (是否合法, 错误信息)
        """
        # 默认校验：如果需要目标但没选目标，或者索引越界等通用逻辑可以在这里做，
        # 但目前我们主要在子类实现具体逻辑。
        return True, ""

    @abstractmethod
    def execute(self, room: 'GameRoom', player: 'PlayerState', card: 'Card', target_sid: Optional[str]) -> Tuple[bool, str]:
        """
        执行卡牌的核心逻辑
        :return: (执行是否成功, 提示信息)
        """
        pass