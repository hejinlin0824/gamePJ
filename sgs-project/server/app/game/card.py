from enum import Enum
from pydantic import BaseModel
from typing import Optional

# === 1. 卡牌类型枚举 ===
class CardType(str, Enum):
    BASIC = "basic"              # 基本牌 (杀、闪、桃、酒)
    STRATEGY = "strategy"        # 锦囊牌 (无中生有、顺手牵羊、过河拆桥等)
    EQUIP_WEAPON = "weapon"      # 装备：武器
    EQUIP_ARMOR = "armor"        # 装备：防具
    EQUIP_HORSE_PLUS = "horse_plus"   # 装备：+1马 (防御)
    EQUIP_HORSE_MINUS = "horse_minus" # 装备：-1马 (进攻)

# === 2. 卡牌数据模型 ===
class Card(BaseModel):
    card_id: str                 # 唯一标识符 (例如: c1, c2...)
    name: str                    # 名称 (例如: 杀, 麒麟弓, +1马)
    suit: str                    # 花色 (heart, spade, club, diamond)
    number: int                  # 点_数 (1-13)
    card_type: CardType          # 类型
    
    # --- 扩展属性 ---
    distance_limit: int = 0      # 某些锦囊的距离限制 (如顺手牵羊为1，其余为0表示无限制)
    attack_range: int = 1        # 🌟 武器的攻击范围。默认为1，高级武器(如麒麟弓)会设置更高