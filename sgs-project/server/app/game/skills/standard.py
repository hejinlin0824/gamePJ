from typing import Optional, Tuple, TYPE_CHECKING
from app.game.skills.core import CardSkill
from app.game.card import Card, CardType
from app.game.enums import PendingType

if TYPE_CHECKING:
    from app.game.room import GameRoom
    from app.game.player import Player

def consume_card_from_hand(player: 'Player', card: Card, room: 'GameRoom', to_discard: bool = True):
    if card in player.hand_cards:
        player.hand_cards.remove(card)
    if to_discard:
        room.deck.discard_pile.append(card)

# === 1. 装备牌技能 ===
class EquipSkill(CardSkill):
    @property
    def name(self) -> str:
        return "equip" 

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        is_weapon = card.card_type == CardType.EQUIP_WEAPON
        is_armor = card.card_type == CardType.EQUIP_ARMOR
        is_horse_plus = card.card_type == CardType.EQUIP_HORSE_PLUS
        is_horse_minus = card.card_type == CardType.EQUIP_HORSE_MINUS

        slot = "weapon" if is_weapon else "armor" if is_armor else \
               "horse_plus" if is_horse_plus else "horse_minus"
        
        # 🌟 修复：使用 equips
        old_item = player.equips.get(slot)
        if old_item:
            room.deck.discard_pile.append(old_item)
        
        if card in player.hand_cards:
            player.hand_cards.remove(card)
        
        # 🌟 修复：使用 equips
        player.equips[slot] = card
        return True, f"成功装配了 {card.name}"

# === 2. 基本牌：杀 ===
class ShaSkill(CardSkill):
    @property
    def name(self) -> str:
        return "杀"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid: return False, "未选择攻击目标"
        if not room.can_attack(player.sid, target_sid):
            return False, f"距离不足"
        if target_sid == player.sid: return False, "不能杀自己"
        
        # 🌟 核心修复：检查出杀限制
        weapon = player.equips.get("weapon")
        has_crossbow = weapon and weapon.name == "诸葛连弩"
        has_paoxiao = "paoxiao" in player.skills # 张飞咆哮
        
        if not has_crossbow and not has_paoxiao and player.sha_count >= 1:
            return False, "本回合出杀次数已耗尽"

        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        from app.game.room import PendingAction 
        consume_card_from_hand(player, card, room)
        
        # 🌟 增加计数
        player.sha_count += 1
        
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=target_sid,
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_SHAN
        )
        return True, "发起攻击，等待对方响应"

# === 3. 基本牌：桃 ===
class TaoSkill(CardSkill):
    @property
    def name(self) -> str:
        return "桃"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if player.hp >= player.max_hp: return False, "体力充沛"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        player.hp += 1
        return True, "回复了1点体力"

# === 4. 锦囊牌：顺手牵羊 ===
class ShunshouSkill(CardSkill):
    @property
    def name(self) -> str:
        return "顺手牵羊"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid: return False, "未选择目标"
        if target_sid == player.sid: return False, "不能对自己使用"
        if room.get_distance(player.sid, target_sid) > 1: return False, "距离过远"
        return True, ""

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        from app.game.room import PendingAction
        consume_card_from_hand(player, card, room)
        
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=player.sid, 
            card_id=card.card_id,
            action_type=PendingType.ASK_FOR_SNATCH,
            extra_data={"target_to_snatch": target_sid}
        )
        return True, "牵羊发动，请选一张牌"

# === 5. 锦囊牌：过河拆桥 ===
class GuoheSkill(CardSkill):
    @property
    def name(self) -> str:
        return "过河拆桥"

    def validate(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        if not target_sid: return False, "未选择目标"
        if target_sid == player.sid: return False, "不能对自己使用"
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
        return True, "拆桥发动，请选择弃牌"

# === 6. 锦囊牌：无中生有 ===
class WuzhongSkill(CardSkill):
    @property
    def name(self) -> str:
        return "无中生有"

    def execute(self, room: 'GameRoom', player: 'Player', card: Card, target_sid: Optional[str]) -> Tuple[bool, str]:
        consume_card_from_hand(player, card, room)
        player.hand_cards.extend(room.deck.draw(2))
        return True, "摸了两张牌"

SKILL_REGISTRY = {
    "杀": ShaSkill(), "桃": TaoSkill(), "顺手牵羊": ShunshouSkill(),
    "过河拆桥": GuoheSkill(), "无中生有": WuzhongSkill(), "equip_handler": EquipSkill() 
}