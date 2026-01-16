from typing import Optional, Tuple, TYPE_CHECKING, List
import random

from app.game.skills.core import CardSkill
from app.game.card import Card, CardType
from app.game.enums import PendingType

if TYPE_CHECKING:
    from app.game.room import GameRoom
    from app.game.player import Player

# --- 工具函数 ---
def consume_card_from_hand(player: 'Player', card: Card, room: 'GameRoom', to_discard: bool = True):
    if card in player.hand_cards:
        player.hand_cards.remove(card)
    else:
        # 容错：按ID查找
        for c in player.hand_cards:
            if c.card_id == card.card_id:
                player.hand_cards.remove(c)
                break
    
    if to_discard:
        room.deck.discard_pile.append(card)

# ==========================================
# 1. 装备牌处理逻辑
# ==========================================
class EquipSkill(CardSkill):
    @property
    def name(self) -> str:
        return "equip_handler"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        slot = "weapon"
        if card.card_type == CardType.EQUIP_ARMOR: slot = "armor"
        elif card.card_type == CardType.EQUIP_HORSE_PLUS: slot = "horse_plus"
        elif card.card_type == CardType.EQUIP_HORSE_MINUS: slot = "horse_minus"
        
        old_item = player.equips.get(slot)
        if old_item:
            room.deck.discard_pile.append(old_item)
        
        consume_card_from_hand(player, card, room, to_discard=False)
        player.equips[slot] = card
        return True, f"装备了 【{card.name}】"

# ==========================================
# 2. 延时锦囊
# ==========================================
class DelayedTrickSkill(CardSkill):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if self._name == "闪电":
            if any(c.name == "闪电" for c in player.judging_cards):
                return False, "判定区已存在闪电"
            return True, ""
        
        # 乐不思蜀
        if not target_sid: return False, "未选择目标"
        if target_sid == player.sid: return False, "不能对自己使用"
        target = room.get_player(target_sid)
        if any(c.name == "乐不思蜀" for c in target.judging_cards):
            return False, "目标判定区已有乐不思蜀"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        target = player if self._name == "闪电" else room.get_player(target_sid)
        consume_card_from_hand(player, card, room, to_discard=False)
        target.judging_cards.append(card)
        return True, f"对 {target.nickname} 使用了 【{card.name}】"

# ==========================================
# 3. 基础牌：杀 / 闪 / 桃
# ==========================================
class ShaSkill(CardSkill):
    @property
    def name(self) -> str:
        return "杀"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid: return False, "未选择目标"
        if target_sid == player.sid: return False, "不能杀自己"
        if not room.can_attack(player.sid, target_sid): return False, "距离不足"
        
        # 诸葛连弩/咆哮检测
        has_crossbow = player.equips.get("weapon") and player.equips["weapon"].name == "诸葛连弩"
        has_unlimited = False
        from app.game.skills.general import GENERAL_SKILL_REGISTRY
        for s in player.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s)
            if skill and skill.has_unlimited_sha(player): has_unlimited = True
        
        if not has_crossbow and not has_unlimited and player.sha_count >= 1:
            return False, "本回合出杀次数已耗尽"

        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        from app.game.room import PendingAction
        consume_card_from_hand(player, card, room)
        player.sha_count += 1
        
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=target_sid,
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_SHAN
        )
        return True, "发起攻击，等待对方出闪"

class TaoSkill(CardSkill):
    @property
    def name(self) -> str:
        return "桃"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if player.hp >= player.max_hp: return False, "体力已满"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        player.hp = min(player.hp + 1, player.max_hp)
        return True, "回复了1点体力"

# ==========================================
# 4. 锦囊：拆 / 顺 / 无中
# ==========================================
class ShunshouSkill(CardSkill):
    @property
    def name(self) -> str:
        return "顺手牵羊"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid or target_sid == player.sid: return False, "无效目标"
        if room.get_distance(player.sid, target_sid) > 1: return False, "距离过远"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        from app.game.room import PendingAction
        consume_card_from_hand(player, card, room)
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=player.sid, # 自己操作
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_SNATCH,
            extra_data={"target_to_snatch": target_sid}
        )
        return True, "请选择要获得的牌"

class GuoheSkill(CardSkill):
    @property
    def name(self) -> str:
        return "过河拆桥"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid or target_sid == player.sid: return False, "无效目标"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        from app.game.room import PendingAction
        consume_card_from_hand(player, card, room)
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=player.sid,
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_DISMANTLE,
            extra_data={"target_to_dismantle": target_sid}
        )
        return True, "请选择要弃置的牌"

class WuzhongSkill(CardSkill):
    @property
    def name(self) -> str:
        return "无中生有"

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        player.hand_cards.extend(room.deck.draw(2))
        return True, "摸了两张牌"

# ==========================================
# 5. 复杂锦囊：决斗 / 借刀 / 桃园 / 五谷 / 南蛮 / 万箭 / 无懈
# ==========================================

class JuedouSkill(CardSkill):
    """【决斗】：出牌阶段，对一名其他角色使用。由其开始，其与你轮流打出一张【杀】，直到有一方不打。"""
    @property
    def name(self) -> str:
        return "决斗"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid or target_sid == player.sid: return False, "需指定一名其他角色"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        from app.game.room import PendingAction
        consume_card_from_hand(player, card, room)
        
        # 决斗逻辑：首先询问目标出杀
        # extra_data 记录 "duel_source" (发起者)，用于轮询逻辑回弹
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=target_sid,
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_SHA, # 必须在 enums.py 添加 ASK_FOR_SHA
            extra_data={
                "is_duel": True, 
                "duel_source": player.sid, 
                "duel_target": target_sid,
                "current_turn": target_sid # 当前该谁出杀
            }
        )
        return True, "决斗开始！等待对方出杀"

class JiedaoSkill(CardSkill):
    """【借刀杀人】：对有武器的角色使用，令其杀指定角色或交出武器"""
    @property
    def name(self) -> str:
        return "借刀杀人"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid: return False, "未选择目标"
        target = room.get_player(target_sid)
        if not target.equips.get("weapon"): return False, "目标没有装备武器"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        from app.game.room import PendingAction
        consume_card_from_hand(player, card, room)
        
        # 借刀逻辑稍微复杂，需要前端先选“借谁的刀”，再选“杀谁”
        # 这里简化为：前端 play_card 时已经传了 target_sid (被借刀的人)
        # 我们需要在 extra_data 里记录“要杀谁”，但这需要前端支持 play_card 传两个目标
        # 暂时简化：服务器挂起，让被借刀的人选择“给武器”或“选择一名角色出杀”
        
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=target_sid,
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_COLLATERAL # 需在 enums 添加
        )
        return True, "等待对方响应：出杀或交出武器"

class TaoyuanSkill(CardSkill):
    """【桃园结义】：全体回1血"""
    @property
    def name(self) -> str:
        return "桃园结义"

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        for p in room.players:
            if p.is_alive and p.hp < p.max_hp:
                p.hp += 1
                room.notify_room(room.room_id, f"🍑 {p.nickname} 回复了1点体力")
        return True, "桃园结义，万物复苏"

class NanmanSkill(CardSkill):
    """【南蛮入侵】：所有其他人出杀，否则掉血"""
    @property
    def name(self) -> str:
        return "南蛮入侵"

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        return self._start_aoe(room, player, card, PendingType.ASK_FOR_SHA)

    def _start_aoe(self, room: 'GameRoom', source: 'Player', card: Card, action_type: PendingType):
        # 构建受害者队列 (逆时针，排除自己)
        targets = []
        idx = room.players.index(source)
        count = len(room.players)
        for i in range(1, count):
            p = room.players[(idx + i) % count]
            if p.is_alive:
                targets.append(p.sid)
        
        if not targets: return True, "场上无其他存活角色"

        # 启动第一个询问
        from app.game.room import PendingAction
        first_target = targets[0]
        room.pending_action = PendingAction(
            source_sid=source.sid,
            target_sid=first_target,
            card_id=card.card_id,
            action_type=action_type,
            extra_data={
                "aoe_targets": targets, # 完整队列
                "current_index": 0,     # 当前进度
                "card_name": card.name
            }
        )
        return True, f"{card.name}！轮流响应中..."

class WanjianSkill(NanmanSkill): # 复用 AOE 逻辑
    """【万箭齐发】：所有其他人出闪，否则掉血"""
    @property
    def name(self) -> str:
        return "万箭齐发"

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        return self._start_aoe(room, player, card, PendingType.ASK_FOR_SHAN)

class WuguSkill(CardSkill):
    """【五谷丰登】：亮出 N 张牌，轮流选择"""
    @property
    def name(self) -> str:
        return "五谷丰登"

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        
        # 1. 亮牌
        alive_count = len([p for p in room.players if p.is_alive])
        wugu_cards = room.deck.draw(alive_count)
        
        # 这里的 public_pile 建议在 GameRoom 中定义一个临时字段，或者直接放在 extra_data
        # 为了前端展示，放在 extra_data 最方便
        
        # 2. 构建轮询队列 (从自己开始)
        targets = []
        idx = room.players.index(player)
        count = len(room.players)
        for i in range(count):
            p = room.players[(idx + i) % count]
            if p.is_alive:
                targets.append(p.sid)

        from app.game.room import PendingAction
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=targets[0],
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_CHOOSE_CARD, # 需在 enums 添加
            extra_data={
                "wugu_cards": [c.model_dump() for c in wugu_cards],
                "aoe_targets": targets,
                "current_index": 0
            }
        )
        # 广播一下亮出的牌
        card_names = "、".join([c.name for c in wugu_cards])
        return True, f"五谷丰登！亮出了: {card_names}"

class WuxieSkill(CardSkill):
    """【无懈可击】：抵消锦囊 (作为响应牌使用)"""
    @property
    def name(self) -> str:
        return "无懈可击"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        # 只能在有 PendingAction 且是锦囊结算时使用
        # 由于逻辑极其复杂（此时是别人的回合），主要作为 handle_response 的 payload 使用
        # 这里的 validate 主要用于 "是否能点得动"
        if not room.pending_action: return False, "当前无锦囊可抵消"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        # 通常不直接由 play_card 调用，而是由 respond_action 调用
        # 如果非要主动用，那就是取消当前的 PendingAction
        if room.pending_action:
            consume_card_from_hand(player, card, room)
            room.pending_action = None # 简单粗暴抵消
            return True, "无懈可击！锦囊失效"
        return False, "无效使用"

# ==========================================
# 注册表
# ==========================================
SKILL_REGISTRY = {
    # 基础
    "equip_handler": EquipSkill(),
    "杀": ShaSkill(),
    "闪": None, 
    "桃": TaoSkill(),
    
    # 锦囊
    "无中生有": WuzhongSkill(),
    "顺手牵羊": ShunshouSkill(),
    "过河拆桥": GuoheSkill(),
    "决斗": JuedouSkill(),
    "借刀杀人": JiedaoSkill(),
    "桃园结义": TaoyuanSkill(),
    "南蛮入侵": NanmanSkill(),
    "万箭齐发": WanjianSkill(),
    "五谷丰登": WuguSkill(),
    "无懈可击": WuxieSkill(),
    
    # 延时
    "乐不思蜀": DelayedTrickSkill("乐不思蜀"),
    "闪电": DelayedTrickSkill("闪电"),
}