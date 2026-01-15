from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .card import Card

class Player(BaseModel):
    # === 基础连接信息 ===
    sid: str
    seat_id: int
    is_host: bool = False
    is_ready: bool = False
    
    # === 用户身份信息 ===
    username: str = ""          
    nickname: str = "无名氏"     
    avatar: str = "default.png" 
    
    # === 武将信息 ===
    general_id: str = ""        
    general_candidates: List[str] = [] 
    kingdom: str = "god"        
    skills: List[str] = []      

    # === 游戏数值状态 ===
    hp: int = 4
    max_hp: int = 4
    is_alive: bool = True
    
    # === 区域 ===
    hand_cards: List[Card] = [] 
    
    # 装备区
    equips: Dict[str, Optional[Card]] = {
        "weapon": None,
        "armor": None,
        "horse_plus": None,
        "horse_minus": None
    }
    
    judging_cards: List[Card] = []

    # 🌟 新增：本回合出杀计数 (解决无限杀Bug)
    sha_count: int = 0 

    @property
    def card_count(self) -> int:
        return len(self.hand_cards)