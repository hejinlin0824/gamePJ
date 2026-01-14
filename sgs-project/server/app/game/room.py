from enum import Enum
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel
from .card import Card
from .engine import GameDeck 

# === 1. 定义完整的游戏阶段 ===
class GamePhase(str, Enum):
    WAITING = "waiting"         # 等待大厅 (准备阶段)
    START = "start"             # 回合开始
    JUDGE = "judge"             # 判定阶段
    DRAW = "draw"               # 摸牌阶段
    PLAY = "play"               # 出牌阶段
    DISCARD = "discard"         # 弃牌阶段
    FINISH = "finish"           # 回合结束
    GAME_OVER = "game_over"     # 游戏结束

# === 2. 玩家状态模型 ===
class PlayerState(BaseModel):
    sid: str
    seat_id: int
    hp: int = 4
    max_hp: int = 4
    hand_cards: List[Card] = []
    equip_area: Dict[str, Optional[Card]] = {
        "weapon": None, "armor": None, "horse_plus": None, "horse_minus": None
    }
    judge_area: List[Card] = []
    is_alive: bool = True
    is_ready: bool = False      # 🌟 新增：准备状态
    is_host: bool = False        # 🌟 新增：房主标记

# === 3. 游戏房间核心类 ===
class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: List[PlayerState] = []
        self.current_player_idx: int = 0
        self.phase: GamePhase = GamePhase.WAITING
        self.is_started: bool = False
        self.deck = GameDeck()  # 每个房间独立的牌堆

    # --- 房间成员管理 ---

    def add_player(self, sid: str) -> Tuple[bool, str]:
        """加入房间逻辑"""
        if self.is_started:
            return False, "游戏已经开始，无法加入"
        
        # 检查是否重复加入
        for p in self.players:
            if p.sid == sid:
                return True, "已在房间中"

        if len(self.players) >= 8:
            return False, "房间已满 (最大8人)"

        # 规则：第一个进入的人是房主，且房主默认已准备
        is_first = len(self.players) == 0
        new_player = PlayerState(
            sid=sid, 
            seat_id=len(self.players),
            is_host=is_first,
            is_ready=is_first 
        )
        
        self.players.append(new_player)
        return True, "成功加入房间"

    def remove_player(self, sid: str):
        """退出房间逻辑"""
        player_to_remove = self.get_player(sid)
        if not player_to_remove:
            return

        was_host = player_to_remove.is_host
        # 从列表移除
        self.players = [p for p in self.players if p.sid != sid]

        # 房主继承逻辑：如果房主走了，且房间里还有人，把房主权交给第一顺位的人
        if was_host and self.players:
            self.players[0].is_host = True
            self.players[0].is_ready = True # 继承者自动设为准备
        
        # 重新排座位号，保证索引连续
        for i, p in enumerate(self.players):
            p.seat_id = i

    def get_player(self, sid: str) -> Optional[PlayerState]:
        for p in self.players:
            if p.sid == sid:
                return p
        return None

    # --- 准备与房主权力 ---

    def toggle_ready(self, sid: str) -> bool:
        """切换准备状态 (房主不可切换，永远是准备)"""
        player = self.get_player(sid)
        if player and not player.is_host:
            player.is_ready = not player.is_ready
            return True
        return False

    def kick_player(self, host_sid: str, target_sid: str) -> Tuple[bool, str]:
        """房主踢人"""
        host = self.get_player(host_sid)
        if not host or not host.is_host:
            return False, "只有房主可以踢人"
        
        if host_sid == target_sid:
            return False, "不能踢出你自己"

        target = self.get_player(target_sid)
        if not target:
            return False, "目标玩家不存在"

        self.remove_player(target_sid)
        return True, "玩家已被踢出"

    def can_start(self) -> Tuple[bool, str]:
        """检查是否具备开始条件"""
        if len(self.players) < 2:
            return False, "房间至少需要 2 名玩家才能开始"
        
        # 检查是否全员准备
        not_ready_count = len([p for p in self.players if not p.is_ready])
        if not_ready_count > 0:
            return False, f"还有 {not_ready_count} 名玩家未准备就绪"
        
        return True, "准备就绪"

    # --- 游戏流程管理 ---

    def start_game(self) -> Tuple[bool, str]:
        """正式开始游戏循环"""
        ready_check, msg = self.can_start()
        if not ready_check:
            return False, msg

        self.is_started = True
        self.deck.init_deck()
        self.deck.shuffle()

        # 初始发牌
        for p in self.players:
            p.hp = p.max_hp
            p.hand_cards = self.deck.draw(4)
            p.is_alive = True

        self.current_player_idx = 0
        self._enter_turn_cycle(self.players[0])
        return True, "游戏开始"

    def _enter_turn_cycle(self, player: PlayerState):
        """进入一个玩家的回合闭环"""
        self.phase = GamePhase.START
        # 此处可扩展：判定阶段、摸牌阶段
        self.phase = GamePhase.DRAW
        player.hand_cards.extend(self.deck.draw(2))
        # 停留在出牌阶段等待操作
        self.phase = GamePhase.PLAY

    def try_end_turn(self, sid: str) -> Tuple[bool, str]:
        """尝试结束回合"""
        current_p = self.players[self.current_player_idx]
        if current_p.sid != sid:
            return False, "不是你的回合"

        # 弃牌规则检查 (手牌不能超过当前血量)
        hand_count = len(current_p.hand_cards)
        limit = max(0, current_p.hp)
        if hand_count > limit:
            # 完整逻辑应在此返回错误让玩家手动弃牌
            # 为了交互平滑，我们执行“自动弃置最后手牌”
            for _ in range(hand_count - limit):
                card = current_p.hand_cards.pop()
                self.deck.discard_pile.append(card)
        
        self.phase = GamePhase.FINISH
        # 切换到下一位生存玩家
        for _ in range(len(self.players)):
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            next_p = self.players[self.current_player_idx]
            if next_p.is_alive:
                self._enter_turn_cycle(next_p)
                break
        
        return True, "回合已切换"

    def play_card(self, sid: str, card_index: int, target_sid: Optional[str]) -> Tuple[bool, str, Optional[Card]]:
        """执行出牌逻辑"""
        current_p = self.players[self.current_player_idx]
        if current_p.sid != sid: return False, "不是你的回合", None
        if self.phase != GamePhase.PLAY: return False, "当前不在出牌阶段", None
        if card_index >= len(current_p.hand_cards): return False, "下标越界", None

        card = current_p.hand_cards[card_index]

        # 基础规则校验
        if card.name == "杀":
            if not target_sid: return False, "【杀】必须指定目标", None
            if target_sid == sid: return False, "不能对自己使用【杀】", None
            target = self.get_player(target_sid)
            if not target or not target.is_alive: return False, "目标不存在或已阵亡", None

        # 消耗手牌
        played_card = current_p.hand_cards.pop(card_index)
        self.deck.discard_pile.append(played_card)
        return True, "成功出牌", played_card

    def apply_damage(self, target_sid: str, amount: int = 1):
        """处理伤害结算"""
        target = self.get_player(target_sid)
        if target:
            target.hp -= amount
            if target.hp <= 0:
                target.is_alive = False
                # 死亡瞬间清空手牌进入弃牌堆
                self.deck.discard_pile.extend(target.hand_cards)
                target.hand_cards = []

    def get_public_state(self):
        """返回房间所有人的可见状态"""
        return {
            "room_id": self.room_id,
            "phase": self.phase,
            "current_seat": self.current_player_idx,
            "is_started": self.is_started,
            "deck_count": len(self.deck.draw_pile),
            "players": [
                {
                    "sid": p.sid,
                    "seat_id": p.seat_id,
                    "hp": p.hp,
                    "max_hp": p.max_hp,
                    "card_count": len(p.hand_cards),
                    "is_current": (i == self.current_player_idx),
                    "is_alive": p.is_alive,
                    "is_ready": p.is_ready,
                    "is_host": p.is_host
                }
                for i, p in enumerate(self.players)
            ]
        }