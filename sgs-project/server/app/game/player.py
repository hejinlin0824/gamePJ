from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .card import Card

class Player(BaseModel):
    sid: str
    seat_id: int
    is_host: bool = False
    is_ready: bool = False
    
    # === 🌟 新增：用户身份信息 ===
    username: str = ""          # 账号 (用于唯一标识)
    nickname: str = "无名氏"     # 昵称 (显示在头像下)
    avatar: str = "default.png" # 头像文件名
    
    # === 游戏数值状态 ===
    hp: int = 4
    max_hp: int = 4
    is_alive: bool = True
    
    # === 区域 ===
    hand_cards: List[Card] = [] # 手牌
    
    # 装备区: key为类型(weapon/armor...), value为装备牌名称(str)
    equips: Dict[str, Optional[str]] = {
        "weapon": None,
        "armor": None,
        "horse_plus": None,
        "horse_minus": None
    }
    
    # 判定区
    judging_cards: List[Card] = []

    @property
    def card_count(self) -> int:
        """计算属性：手牌数量（前端不展示具体牌时使用）"""
        return len(self.hand_cards)