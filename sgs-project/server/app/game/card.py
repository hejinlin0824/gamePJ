from enum import Enum
from pydantic import BaseModel

class CardSuit(str, Enum):
    SPADE = "spade"     # 黑桃 ♠
    HEART = "heart"     # 红桃 ♥
    CLUB = "club"       # 梅花 ♣
    DIAMOND = "diamond" # 方片 ♦
    NONE = "none"       # 无花色 (特殊牌)

class CardType(str, Enum):
    BASIC = "basic"         # 基本牌 (杀闪桃)
    SCROLL = "scroll"       # 锦囊牌 (过河拆桥等)
    EQUIP = "equip"         # 装备牌
    DELAYED_SCROLL = "delayed" # 延时锦囊 (乐不思蜀)

class Card(BaseModel):
    card_id: str        # 唯一ID (例如 "sha-spade-7")
    name: str           # 名称 (杀)
    suit: CardSuit      # 花色
    rank: int           # 点数 (1-13)
    type: CardType      # 类型
    image: str = ""     # 图片文件名 (预留)
    description: str = "" # 描述

    class Config:
        use_enum_values = True