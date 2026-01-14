from enum import Enum
from typing import List, Optional, Dict, Tuple, Any
from pydantic import BaseModel
from .card import Card, CardType
from .engine import GameDeck 

# === 1. 核心状态枚举 ===

class GamePhase(str, Enum):
    WAITING = "waiting"         # 大厅等待
    START = "start"             # 回合开始
    JUDGE = "judge"             # 判定阶段
    DRAW = "draw"               # 摸牌阶段
    PLAY = "play"               # 出牌阶段
    DISCARD = "discard"         # 弃牌阶段
    FINISH = "finish"           # 回合结束
    GAME_OVER = "game_over"     # 游戏结束

class PendingType(str, Enum):
    """服务器挂起类型：必须等待玩家操作才能继续游戏"""
    ASK_FOR_SHAN = "ask_for_shan"            # 被杀者响应闪
    ASK_FOR_DISMANTLE = "ask_for_dismantle"  # 发起者选牌拆除
    ASK_FOR_SNATCH = "ask_for_snatch"        # 发起者选牌顺走

# === 2. 核心数据模型 ===

class PendingAction(BaseModel):
    """当前正在等待的交互详情"""
    source_sid: str                          
    target_sid: str                          
    card_id: Optional[str] = None            
    action_type: PendingType                 
    extra_data: Dict[str, Any] = {}          

class PlayerState(BaseModel):
    """玩家全量状态模型"""
    sid: str
    seat_id: int
    hp: int = 4
    max_hp: int = 4
    hand_cards: List[Card] = []
    # 装备区：weapon(武器), armor(防具), horse_plus(+1马), horse_minus(-1马)
    equip_area: Dict[str, Optional[Card]] = {
        "weapon": None, "armor": None, "horse_plus": None, "horse_minus": None
    }
    is_alive: bool = True
    is_ready: bool = False
    is_host: bool = False

# === 3. 房间逻辑引擎核心 ===

class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: List[PlayerState] = []
        self.current_player_idx: int = 0
        self.phase: GamePhase = GamePhase.WAITING
        self.is_started: bool = False
        self.deck = GameDeck()
        self.pending_action: Optional[PendingAction] = None
        self.winner_sid: Optional[str] = None # 胜利者标识

    # --- 基础管理 (房主、准备、移除) ---

    def get_player(self, sid: str) -> Optional[PlayerState]:
        for p in self.players:
            if p.sid == sid: return p
        return None

    def add_player(self, sid: str) -> Tuple[bool, str]:
        if self.is_started: return False, "游戏已开始"
        if len(self.players) >= 8: return False, "房间已满"
        if self.get_player(sid): return True, "已在房间内"

        is_first = len(self.players) == 0
        new_player = PlayerState(
            sid=sid, seat_id=len(self.players), is_host=is_first, is_ready=is_first
        )
        self.players.append(new_player)
        return True, "加入成功"

    def remove_player(self, sid: str):
        p = self.get_player(sid)
        if not p: return
        was_host = p.is_host
        self.players = [pl for pl in self.players if pl.sid != sid]
        if was_host and self.players:
            self.players[0].is_host, self.players[0].is_ready = True, True
        for i, pl in enumerate(self.players): pl.seat_id = i

    def kick_player(self, host_sid: str, target_sid: str) -> Tuple[bool, str]:
        host = self.get_player(host_sid)
        if not host or not host.is_host: return False, "权限不足"
        if host_sid == target_sid: return False, "不能踢自己"
        self.remove_player(target_sid)
        return True, "踢出成功"

    def toggle_ready(self, sid: str):
        p = self.get_player(sid)
        if p and not p.is_host: p.is_ready = not p.is_ready
        return True

    # --- 核心属性：距离计算与攻击范围 ---

    def get_distance(self, from_sid: str, to_sid: str) -> int:
        """计算最终距离 = 物理环距 + 防御马修正 - 进攻马修正"""
        p1, p2 = self.get_player(from_sid), self.get_player(to_sid)
        if not p1 or not p2: return 999
        
        n = len(self.players)
        diff = abs(p1.seat_id - p2.seat_id)
        phys_dist = min(diff, n - diff)
        
        plus_mod = 1 if p2.equip_area["horse_plus"] else 0
        minus_mod = 1 if p1.equip_area["horse_minus"] else 0
        
        return max(1, phys_dist + plus_mod - minus_mod)

    def can_attack(self, from_sid: str, to_sid: str) -> bool:
        """检查武器攻击范围是否够得到目标"""
        p = self.get_player(from_sid)
        if not p: return False
        # 如果装了武器，取武器的范围属性，否则默认范围为 1
        weapon = p.equip_area["weapon"]
        attack_range = weapon.attack_range if weapon else 1
        
        actual_dist = self.get_distance(from_sid, to_sid)
        return attack_range >= actual_dist

    # --- 游戏全生命周期 ---

    def start_game(self) -> Tuple[bool, str]:
        if len(self.players) < 2: return False, "人数不足2人"
        if not all(p.is_ready for p in self.players): return False, "仍有玩家未准备"
        
        self.is_started = True
        self.winner_sid = None
        self.deck.init_deck()
        self.deck.shuffle()
        for p in self.players:
            p.hp, p.is_alive = p.max_hp, True
            p.hand_cards = self.deck.draw(4)
            p.equip_area = {k: None for k in p.equip_area}

        self.current_player_idx = 0
        self._enter_turn_cycle(self.players[0])
        return True, "游戏开始"

    def _enter_turn_cycle(self, player: PlayerState):
        """阶段流转：判定 -> 摸牌 -> 出牌"""
        self.phase = GamePhase.DRAW
        player.hand_cards.extend(self.deck.draw(2))
        self.phase = GamePhase.PLAY

    def try_end_turn(self, sid: str) -> Tuple[bool, str]:
        """结束回合：执行弃牌逻辑"""
        if self.pending_action: return False, "有待处理的询问，无法结束"
        
        p = self.players[self.current_player_idx]
        if p.sid != sid: return False, "非当前回合玩家"

        # 弃牌：手牌数必须等于体力
        limit = max(0, p.hp)
        while len(p.hand_cards) > limit:
            c = p.hand_cards.pop()
            self.deck.discard_pile.append(c)
        
        # 移交回合到下一存活玩家
        for _ in range(len(self.players)):
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            next_p = self.players[self.current_player_idx]
            if next_p.is_alive:
                self._enter_turn_cycle(next_p)
                break
        return True, "回合已结束"

    # --- 🌟 核心战斗与装备逻辑 ---

    def play_card(self, sid: str, index: int, target_sid: Optional[str]) -> Tuple[bool, str, Optional[Card]]:
        """主动出牌行为核心判断"""
        if self.pending_action or self.phase == GamePhase.GAME_OVER: 
            return False, "当前禁止此项操作", None
        
        p = self.get_player(sid)
        if not p or self.players[self.current_player_idx].sid != sid: 
            return False, "不是你的回合", None
        if index >= len(p.hand_cards): 
            return False, "手牌索引无效", None
        
        card = p.hand_cards[index]

        # 🌟 核心：通用装备逻辑（修复了你的武器逻辑消失问题）
        # 只要卡牌类型属于四大类装备，就执行替换逻辑
        is_weapon = card.card_type == CardType.EQUIP_WEAPON
        is_armor = card.card_type == CardType.EQUIP_ARMOR
        is_horse_plus = card.card_type == CardType.EQUIP_HORSE_PLUS
        is_horse_minus = card.card_type == CardType.EQUIP_HORSE_MINUS

        if is_weapon or is_armor or is_horse_plus or is_horse_minus:
            slot = "weapon" if is_weapon else "armor" if is_armor else \
                   "horse_plus" if is_horse_plus else "horse_minus"
            
            # 将旧装备放入弃牌堆
            old_item = p.equip_area[slot]
            if old_item: self.deck.discard_pile.append(old_item)
            
            # 穿上新装备（此时 Card 对象的 attack_range 等属性已在对象中）
            p.equip_area[slot] = p.hand_cards.pop(index)
            return True, f"成功装配了 {card.name}", card

        # --- 基础牌逻辑 ---

        if card.name == "杀":
            if not target_sid: return False, "未选择攻击目标", None
            if not self.can_attack(sid, target_sid): 
                return False, f"距离不足（当前距离 {self.get_distance(sid, target_sid)}）", None
            
            played = p.hand_cards.pop(index)
            self.deck.discard_pile.append(played)
            # 挂起等待目标出闪
            self.pending_action = PendingAction(
                source_sid=sid, target_sid=target_sid, card_id=played.card_id,
                action_type=PendingType.ASK_FOR_SHAN
            )
            return True, "发起攻击，等待对方响应", played

        if card.name == "顺手牵羊":
            if not target_sid: return False, "未选择目标", None
            if self.get_distance(sid, target_sid) > 1: return False, "距离过远，无法顺手牵羊", None
            
            played = p.hand_cards.pop(index)
            self.deck.discard_pile.append(played)
            # 挂起等待发起者选牌
            self.pending_action = PendingAction(
                source_sid=sid, target_sid=sid, card_id=played.card_id,
                action_type=PendingType.ASK_FOR_SNATCH,
                extra_data={"target_to_snatch": target_sid}
            )
            return True, "牵羊发动，请选一张牌", played

        if card.name == "过河拆桥":
            if not target_sid: return False, "未选择目标", None
            played = p.hand_cards.pop(index)
            self.deck.discard_pile.append(played)
            # 挂起等待发起者选牌
            self.pending_action = PendingAction(
                source_sid=sid, target_sid=sid, card_id=played.card_id,
                action_type=PendingType.ASK_FOR_DISMANTLE,
                extra_data={"target_to_dismantle": target_sid}
            )
            return True, "拆桥发动，请选择弃牌", played

        if card.name == "桃":
            if p.hp >= p.max_hp: return False, "体力充沛，无需回复", None
            p.hand_cards.pop(index); self.deck.discard_pile.append(card); p.hp += 1
            return True, "回复了1点体力", card

        if card.name == "无中生有":
            p.hand_cards.pop(index); self.deck.discard_pile.append(card)
            p.hand_cards.extend(self.deck.draw(2))
            return True, "摸了两张牌", card

        return False, f"卡牌 【{card.name}】 逻辑尚未在引擎中定义", None

    # --- 🌟 响应与结算核心 ---

    def handle_response(self, sid: str, card_index: Optional[int], target_area: Optional[str] = None) -> Tuple[bool, str]:
        """处理询问状态下的玩家操作"""
        if not self.pending_action or self.pending_action.target_sid != sid: 
            return False, "当前无须你做出响应"
        
        act = self.pending_action
        p_self = self.get_player(sid)

        # 1. 响应【杀】
        if act.action_type == PendingType.ASK_FOR_SHAN:
            if card_index is not None:
                c = p_self.hand_cards[card_index]
                if c.name == "闪":
                    p_self.hand_cards.pop(card_index); self.deck.discard_pile.append(c)
                    self.pending_action = None
                    return True, "已出【闪】，成功抵消攻击"
            # 跳过或没闪
            self.apply_damage(sid, 1)
            self.pending_action = None
            return True, "未响应【闪】，受到了1点伤害"

        # 2. 响应【拆桥】(丢牌入弃牌堆)
        if act.action_type == PendingType.ASK_FOR_DISMANTLE:
            target_p = self.get_player(act.extra_data["target_to_dismantle"])
            if not target_p: return False, "目标已离线"
            self._move_card(target_p, p_self, target_area, to_hand=False)
            self.pending_action = None
            return True, "已成功拆除对方的牌"

        # 3. 响应【顺手】(牌归自己手牌)
        if act.action_type == PendingType.ASK_FOR_SNATCH:
            target_p = self.get_player(act.extra_data["target_to_snatch"])
            if not target_p: return False, "目标已离线"
            # 🌟 to_hand=True 居为己用
            self._move_card(target_p, p_self, target_area, to_hand=True)
            self.pending_action = None
            return True, "顺手牵羊成功，牌已归入你的手牌"

        return False, "无效的操作响应"

    def _move_card(self, from_p: PlayerState, to_p: PlayerState, area: str, to_hand: bool):
        """内部工具：在玩家间移动卡牌"""
        card = None
        # 移出手牌
        if area == "hand" and from_p.hand_cards:
            card = from_p.hand_cards.pop(0) 
        # 移出装备
        elif area in from_p.equip_area:
            card = from_p.equip_area[area]
            if card: from_p.equip_area[area] = None
        
        # 转移去向
        if card:
            if to_hand: to_p.hand_cards.append(card)
            else: self.deck.discard_pile.append(card)

    def apply_damage(self, sid: str, amount: int):
        """执行扣血及🌟 胜利者检测"""
        p = self.get_player(sid)
        if p:
            p.hp -= amount
            if p.hp <= 0:
                p.is_alive = False
                # 阵亡遗产处理：所有牌入弃牌堆
                self.deck.discard_pile.extend(p.hand_cards); p.hand_cards = []
                for k in p.equip_area: 
                    if p.equip_area[k]: 
                        self.deck.discard_pile.append(p.equip_area[k])
                        p.equip_area[k] = None
                
                # 🌟 检测全场胜负
                alive_players = [pl for pl in self.players if pl.is_alive]
                if len(alive_players) <= 1:
                    self.phase = GamePhase.GAME_OVER
                    if alive_players: self.winner_sid = alive_players[0].sid

    def get_public_state(self):
        """全量状态导出"""
        return {
            "room_id": self.room_id, "phase": self.phase, "current_seat": self.current_player_idx,
            "is_started": self.is_started, "deck_count": len(self.deck.draw_pile),
            "pending": self.pending_action.model_dump() if self.pending_action else None,
            "winner_sid": self.winner_sid,
            "players": [
                {
                    "sid": p.sid, "seat_id": p.seat_id, "hp": p.hp, "max_hp": p.max_hp,
                    "is_alive": p.is_alive, "is_ready": p.is_ready, "is_host": p.is_host,
                    "card_count": len(p.hand_cards),
                    "equips": {k: (v.name if v else None) for k, v in p.equip_area.items()}
                } for p in self.players
            ]
        }