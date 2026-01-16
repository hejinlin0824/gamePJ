from abc import ABC
from typing import TYPE_CHECKING, List, Optional, Tuple
import random

from app.game.card import Card, CardType
from app.game.enums import PendingType

if TYPE_CHECKING:
    from app.game.room import GameRoom
    from app.game.player import Player

class GeneralSkill(ABC):
    """
    武将技能基类 (策略模式)
    包含游戏流程中的各种 '钩子(Hooks)'
    """
    def __init__(self, name: str):
        self.name = name

    # --- 1. 属性修正类钩子 ---
    def modify_distance(self, room: 'GameRoom', from_player: 'Player', to_player: 'Player', distance: int) -> int:
        """[钩子] 修改计算出的距离 (如：马术)"""
        return distance

    def modify_draw_count(self, room: 'GameRoom', player: 'Player', count: int) -> int:
        """[钩子] 修改摸牌数量 (如：英姿)"""
        return count

    def modify_hand_limit(self, room: 'GameRoom', player: 'Player', limit: int) -> int:
        """[钩子] 修改手牌上限 (如：权计，吕蒙-克己逻辑在弃牌阶段处理)"""
        return limit

    # --- 2. 卡牌转化类钩子 ---
    def can_transform_card(self, player: 'Player', card: Card, as_card_name: str) -> bool:
        """[钩子] 转化技：判断手牌 card 是否可以当做 as_card_name 使用 (如：龙胆、武圣)"""
        return False

    # --- 3. 规则豁免类钩子 ---
    def has_unlimited_sha(self, player: 'Player') -> bool:
        """[钩子] 是否无限出杀 (如：咆哮)"""
        return False

    def can_avoid_target(self, room: 'GameRoom', user: 'Player', target: 'Player', card_name: str) -> bool:
        """[钩子] 是否可以豁免成为目标 (如：空城、谦逊)"""
        return False

    def attack_requires_two_cards(self, room: 'GameRoom', target: 'Player') -> bool:
        """[钩子] 攻击此人是否需要消耗两张牌 (如：无双)"""
        return False

    # --- 4. 事件触发类钩子 (核心逻辑) ---
    def on_receive_damage(self, room: 'GameRoom', player: 'Player', source: Optional['Player'], amount: int, card: Optional[Card]) -> bool:
        """
        [钩子] 受到伤害后触发
        :return: True 表示技能触发并中断了流程（需要等待前端响应），False 表示无事发生
        """
        return False

    def on_phase_start(self, room: 'GameRoom', player: 'Player', phase: str) -> bool:
        """
        [钩子] 某个阶段开始时触发 (如：洛神在判定阶段前，闭月在结束阶段)
        """
        return False

    def on_use_card(self, room: 'GameRoom', player: 'Player', card: Card) -> bool:
        """[钩子] 使用卡牌结算后触发 (如：集智)"""
        return False

    def on_lose_card(self, room: 'GameRoom', player: 'Player', cards: List[Card], move_type: str) -> bool:
        """[钩子] 失去卡牌后触发 (如：连营、枭姬)"""
        return False


# ==========================================
#                 魏国 (Wei)
# ==========================================

class JianxiongSkill(GeneralSkill):
    """【奸雄】：锁定技，当你受到伤害后，你可以获得对你造成伤害的牌。"""
    def __init__(self): super().__init__("jianxiong")

    def on_receive_damage(self, room: 'GameRoom', player: 'Player', source: Optional['Player'], amount: int, card: Optional[Card]) -> bool:
        # 如果是卡牌造成的伤害，且卡牌还在处理区/弃牌堆（简化逻辑：只要有 card 对象就询问）
        if card:
            # 这是一个询问技能，需要前端确认
            from app.game.room import PendingAction
            room.pending_action = PendingAction(
                source_sid=player.sid,
                target_sid=player.sid,
                action_type=PendingType.ASK_FOR_SKILL_CONFIRM,
                extra_data={
                    "skill_name": "奸雄",
                    "transform_name": "获得伤害牌", # 用于前端显示
                    "card_id": card.card_id,
                    "msg": f"是否发动【奸雄】获得 {card.name}？"
                }
            )
            return True # 中断结算，等待玩家确认
        return False

class HujiaSkill(GeneralSkill):
    """【护驾】：主公技 (需要配合 Room 的响应逻辑，此处主要标记身份)"""
    def __init__(self): super().__init__("hujia")

class TianduSkill(GeneralSkill):
    """【天妒】：在 Room.py 的判定逻辑中直接处理获得判定牌"""
    def __init__(self): super().__init__("tiandu")

class YijiSkill(GeneralSkill):
    """【遗计】：当你受到1点伤害后，你可以摸两张牌，然后你可以将任意数量的牌交给其他角色。"""
    def __init__(self): super().__init__("yiji")

    def on_receive_damage(self, room: 'GameRoom', player: 'Player', source: Optional['Player'], amount: int, card: Optional[Card]) -> bool:
        # 1. 直接摸牌 (每点伤害2张)
        count = amount * 2
        new_cards = room.deck.draw(count)
        player.hand_cards.extend(new_cards)
        room.notify_room(room.room_id, f"⚡ {player.nickname} 发动【遗计】，摸了 {count} 张牌")
        
        # 通知前端更新手牌
        import socketio
        async_task = room.broadcast_room_state(room) # 这一步通常在 room 外部调用，但在 Websocket 框架下需要注意异步
        
        # 2. 设置 PendingAction 等待分牌
        from app.game.room import PendingAction
        room.pending_action = PendingAction(
            source_sid=player.sid,
            target_sid=player.sid,
            action_type=PendingType.ASK_FOR_YIJI,
            extra_data={
                "draw_cards": [c.card_id for c in new_cards], # 标记刚刚摸到的牌
                "draw_count": count
            }
        )
        return True # 中断

class FankuiSkill(GeneralSkill):
    """【反馈】：当你受到伤害后，你可以获得伤害来源的一张牌。"""
    def __init__(self): super().__init__("fankui")

    def on_receive_damage(self, room: 'GameRoom', player: 'Player', source: Optional['Player'], amount: int, card: Optional[Card]) -> bool:
        if source and source.sid != player.sid and (source.hand_cards or any(source.equips.values())):
            from app.game.room import PendingAction
            room.pending_action = PendingAction(
                source_sid=player.sid,
                target_sid=source.sid, # 目标是伤害来源
                action_type=PendingType.ASK_FOR_SNATCH, # 复用顺手牵羊的 UI 逻辑
                extra_data={
                    "skill_name": "反馈",
                    "target_to_snatch": source.sid,
                    "msg": f"是否对 {source.nickname} 发动【反馈】？"
                }
            )
            return True
        return False

class GuicaiSkill(GeneralSkill):
    """【鬼才】：改判 (需要 Room 在判定前询问)"""
    def __init__(self): super().__init__("guicai")

class GanglieSkill(GeneralSkill):
    """【刚烈】：当你受到伤害后，你可以进行判定..."""
    def __init__(self): super().__init__("ganglie")

    def on_receive_damage(self, room: 'GameRoom', player: 'Player', source: Optional['Player'], amount: int, card: Optional[Card]) -> bool:
        if source:
            from app.game.room import PendingAction
            room.pending_action = PendingAction(
                source_sid=player.sid,
                target_sid=player.sid, # 先询问自己是否发动
                action_type=PendingType.ASK_FOR_GANGLIE,
                extra_data={
                    "source_sid": source.sid,
                    "msg": f"是否对 {source.nickname} 发动【刚烈】？"
                }
            )
            return True
        return False

class TuxiSkill(GeneralSkill):
    """【突袭】：摸牌阶段开始时 (需要配合 Draw Phase 逻辑)"""
    def __init__(self): super().__init__("tuxi")

class LuoyiSkill(GeneralSkill):
    """【裸衣】：摸牌阶段少摸一张，伤害+1 (需要配合 Draw Phase 和 Damage Calculation)"""
    def __init__(self): super().__init__("luoyi")

class LuoshenSkill(GeneralSkill):
    """【洛神】：准备阶段开始时，进行判定..."""
    def __init__(self): super().__init__("luoshen")

    def on_phase_start(self, room: 'GameRoom', player: 'Player', phase: str) -> bool:
        if phase == "start": # 准备阶段
            # 简化版：直接进行一次判定，不处理无限循环（防止死循环）
            # 完整版应该是一个递归的 PendingAction，这里为了演示流程，做一次自动判定
            judge = room.deck.draw(1)[0]
            room.deck.discard_pile.append(judge)
            room.notify_room(room.room_id, f"🎲 {player.nickname} 发动【洛神】，判定结果：{judge.suit} {judge.number}")
            
            if judge.suit in ["spade", "club"]: # 黑色
                room.notify_room(room.room_id, "✅ 洛神生效，获得该牌")
                player.hand_cards.append(judge)
                room.deck.discard_pile.remove(judge) # 从弃牌堆拿回来
                # TODO: 这里应该允许继续判定，为了代码结构不崩塌，暂只判一次
            else:
                room.notify_room(room.room_id, "❌ 洛神失效")
            return False # 不中断阶段流转
        return False

class QingguoSkill(GeneralSkill):
    """【倾国】：黑色当闪"""
    def __init__(self): super().__init__("qingguo")
    
    def can_transform_card(self, player: 'Player', card: Card, as_card_name: str) -> bool:
        if as_card_name == "闪" and card.suit in ["spade", "club"]:
            return True
        return False


# ==========================================
#                 蜀国 (Shu)
# ==========================================

class RendeSkill(GeneralSkill):
    """【仁德】：出牌阶段主动技"""
    def __init__(self): super().__init__("rende")

class JijiangSkill(GeneralSkill):
    """【激将】：主公技"""
    def __init__(self): super().__init__("jijiang")

class WushengSkill(GeneralSkill):
    """【武圣】：红色当杀"""
    def __init__(self): super().__init__("wusheng")
    
    def can_transform_card(self, player: 'Player', card: Card, as_card_name: str) -> bool:
        if as_card_name == "杀" and card.suit in ["heart", "diamond"]:
            return True
        return False

class PaoxiaoSkill(GeneralSkill):
    """【咆哮】：无限出杀"""
    def __init__(self): super().__init__("paoxiao")
    
    def has_unlimited_sha(self, player: 'Player') -> bool:
        return True

class GuanxingSkill(GeneralSkill):
    """【观星】：准备阶段看牌堆顶"""
    def __init__(self): super().__init__("guanxing")
    # 需要在 on_phase_start('start') 中处理复杂的 UI 交互，暂留钩子

class KongchengSkill(GeneralSkill):
    """【空城】：无手牌不能成为杀/决斗目标"""
    def __init__(self): super().__init__("kongcheng")
    
    def can_avoid_target(self, room: 'GameRoom', user: 'Player', target: 'Player', card_name: str) -> bool:
        if not target.hand_cards and card_name in ["杀", "决斗"]:
            return True
        return False

class LongdanSkill(GeneralSkill):
    """【龙胆】：杀当闪，闪当杀"""
    def __init__(self): super().__init__("longdan")
    
    def can_transform_card(self, player: 'Player', card: Card, as_card_name: str) -> bool:
        if as_card_name == "杀" and card.name == "闪": return True
        if as_card_name == "闪" and card.name == "杀": return True
        return False

class MashuSkill(GeneralSkill):
    """【马术】：距离-1"""
    def __init__(self): super().__init__("mashu")
    
    def modify_distance(self, room: 'GameRoom', from_player: 'Player', to_player: 'Player', distance: int) -> int:
        return max(1, distance - 1)

class TieqiSkill(GeneralSkill):
    """【铁骑】：使用杀时判定 (需要 on_use_card 钩子)"""
    def __init__(self): super().__init__("tieqi")

    def on_use_card(self, room: 'GameRoom', player: 'Player', card: Card) -> bool:
        if card.name == "杀":
            # 简化版：这里只是打印，完整版需要加入 PendingAction 强行判定
            room.notify_room(room.room_id, f"🐎 {player.nickname} 发动【铁骑】")
        return False

class JizhiSkill(GeneralSkill):
    """【集智】：使用锦囊摸牌"""
    def __init__(self): super().__init__("jizhi")

    def on_use_card(self, room: 'GameRoom', player: 'Player', card: Card) -> bool:
        if card.card_type.name in ["STRATEGY", "SCROLL", "DELAYED"]: # 只要是锦囊
            player.hand_cards.extend(room.deck.draw(1))
            room.notify_room(room.room_id, f"💡 {player.nickname} 发动【集智】，摸了一张牌")
        return False

class QicaiSkill(GeneralSkill):
    """【奇才】：锦囊无距离限制 (逻辑在 Room.check_distance 中处理)"""
    def __init__(self): super().__init__("qicai")


# ==========================================
#                 吴国 (Wu)
# ==========================================

class ZhihengSkill(GeneralSkill):
    """【制衡】：主动技"""
    def __init__(self): super().__init__("zhiheng")

class JiuyuanSkill(GeneralSkill):
    """【救援】：主公技"""
    def __init__(self): super().__init__("jiuyuan")

class QixiSkill(GeneralSkill):
    """【奇袭】：黑色当过河拆桥"""
    def __init__(self): super().__init__("qixi")
    
    def can_transform_card(self, player: 'Player', card: Card, as_card_name: str) -> bool:
        if as_card_name == "过河拆桥" and card.suit in ["spade", "club"]:
            return True
        return False

class KejiSkill(GeneralSkill):
    """【克己】：不出杀手牌上限+ (逻辑在弃牌阶段)"""
    def __init__(self): super().__init__("keji")

class KurouSkill(GeneralSkill):
    """【苦肉】：主动技"""
    def __init__(self): super().__init__("kurou")

class YingziSkill(GeneralSkill):
    """【英姿】：摸牌阶段多摸一张"""
    def __init__(self): super().__init__("yingzi")
    
    def modify_draw_count(self, room: 'GameRoom', player: 'Player', count: int) -> int:
        return count + 1

class FanjianSkill(GeneralSkill):
    """【反间】：主动技"""
    def __init__(self): super().__init__("fanjian")

class GuoseSkill(GeneralSkill):
    """【国色】：方块当乐不思蜀"""
    def __init__(self): super().__init__("guose")
    
    def can_transform_card(self, player: 'Player', card: Card, as_card_name: str) -> bool:
        if as_card_name == "乐不思蜀" and card.suit == "diamond":
            return True
        return False

class LiuliSkill(GeneralSkill):
    """【流离】：转移杀目标 (需配合 Room 的响应链)"""
    def __init__(self): super().__init__("liuli")

class QianxunSkill(GeneralSkill):
    """【谦逊】：不受乐/顺手"""
    def __init__(self): super().__init__("qianxun")
    
    def can_avoid_target(self, room: 'GameRoom', user: 'Player', target: 'Player', card_name: str) -> bool:
        if card_name in ["乐不思蜀", "顺手牵羊"]:
            return True
        return False

class LianyingSkill(GeneralSkill):
    """【连营】：失去手牌后若为0则摸1"""
    def __init__(self): super().__init__("lianying")

    def on_lose_card(self, room: 'GameRoom', player: 'Player', cards: List[Card], move_type: str) -> bool:
        if not player.hand_cards:
            player.hand_cards.extend(room.deck.draw(1))
            room.notify_room(room.room_id, f"🔥 {player.nickname} 发动【连营】，摸了一张牌")
        return False

class JieyinSkill(GeneralSkill):
    """【结姻】：主动技"""
    def __init__(self): super().__init__("jieyin")

class XiaojiSkill(GeneralSkill):
    """【枭姬】：失去装备区牌时摸两张"""
    def __init__(self): super().__init__("xiaoji")

    def on_lose_card(self, room: 'GameRoom', player: 'Player', cards: List[Card], move_type: str) -> bool:
        # 判断失去的牌是否来自装备区 (这需要 room 在调用 hook 时传入 move_type="equip")
        if move_type == "equip":
            count = len(cards) * 2
            if count > 0:
                player.hand_cards.extend(room.deck.draw(count))
                room.notify_room(room.room_id, f"💃 {player.nickname} 发动【枭姬】，摸了 {count} 张牌")
        return False


# ==========================================
#                 群雄 (Qun)
# ==========================================

class QingnangSkill(GeneralSkill):
    """【青囊】：主动技"""
    def __init__(self): super().__init__("qingnang")

class JijiuSkill(GeneralSkill):
    """【急救】：回合外红色当桃 (在 Room 濒死结算时判断)"""
    def __init__(self): super().__init__("jijiu")

class WushuangSkill(GeneralSkill):
    """【无双】：攻击需要两张闪/杀"""
    def __init__(self): super().__init__("wushuang")
    
    def attack_requires_two_cards(self, room: 'GameRoom', target: 'Player') -> bool:
        return True

class LijianSkill(GeneralSkill):
    """【离间】：主动技"""
    def __init__(self): super().__init__("lijian")

class BiyueSkill(GeneralSkill):
    """【闭月】：回合结束阶段摸一张牌"""
    def __init__(self): super().__init__("biyue")

    def on_phase_start(self, room: 'GameRoom', player: 'Player', phase: str) -> bool:
        if phase == "finish": # 结束阶段
            player.hand_cards.extend(room.deck.draw(1))
            room.notify_room(room.room_id, f"🌙 {player.nickname} 发动【闭月】，摸了一张牌")
        return False

class YongsiSkill(GeneralSkill):
    """【庸肆】：摸牌阶段多摸，弃牌阶段多弃 (简化：仅多摸)"""
    def __init__(self): super().__init__("yongsi")
    
    def modify_draw_count(self, room: 'GameRoom', player: 'Player', count: int) -> int:
        return count + 1 # 暂不处理多弃牌的负面效果

class WeidiSkill(GeneralSkill):
    """【伪帝】：拥有主公技"""
    def __init__(self): super().__init__("weidi")

class YaowuSkill(GeneralSkill):
    """【耀武】：锁定技，受红杀伤害，来源摸牌 (on_receive_damage)"""
    def __init__(self): super().__init__("yaowu")
    
    def on_receive_damage(self, room: 'GameRoom', player: 'Player', source: Optional['Player'], amount: int, card: Optional[Card]) -> bool:
        if source and card and card.name == "杀" and card.suit in ["heart", "diamond"]:
            source.hand_cards.extend(room.deck.draw(1))
            room.notify_room(room.room_id, f"👹 {player.nickname} 【耀武】生效，伤害来源摸了一张牌")
        return False

class FuyongSkill(GeneralSkill):
    """【负勇】：濒死不能被救 (Room 逻辑处理)"""
    def __init__(self): super().__init__("fuyong")


# ==========================================
#               技能注册表
# ==========================================
GENERAL_SKILL_REGISTRY = {
    # 魏
    "jianxiong": JianxiongSkill(), "hujia": HujiaSkill(), "tiandu": TianduSkill(),
    "yiji": YijiSkill(), "fankui": FankuiSkill(), "guicai": GuicaiSkill(),
    "ganglie": GanglieSkill(), "tuxi": TuxiSkill(), "luoyi": LuoyiSkill(),
    "luoshen": LuoshenSkill(), "qingguo": QingguoSkill(),
    
    # 蜀
    "rende": RendeSkill(), "jijiang": JijiangSkill(), "wusheng": WushengSkill(),
    "paoxiao": PaoxiaoSkill(), "guanxing": GuanxingSkill(), "kongcheng": KongchengSkill(),
    "longdan": LongdanSkill(), "mashu": MashuSkill(), "tieqi": TieqiSkill(),
    "jizhi": JizhiSkill(), "qicai": QicaiSkill(),
    
    # 吴
    "zhiheng": ZhihengSkill(), "jiuyuan": JiuyuanSkill(), "qixi": QixiSkill(),
    "keji": KejiSkill(), "kurou": KurouSkill(), "yingzi": YingziSkill(),
    "fanjian": FanjianSkill(), "guose": GuoseSkill(), "liuli": LiuliSkill(),
    "qianxun": QianxunSkill(), "lianying": LianyingSkill(), "jieyin": JieyinSkill(),
    "xiaoji": XiaojiSkill(),
    
    # 群
    "qingnang": QingnangSkill(), "jijiu": JijiuSkill(), "wushuang": WushuangSkill(),
    "lijian": LijianSkill(), "biyue": BiyueSkill(), "yongsi": YongsiSkill(),
    "weidi": WeidiSkill(), "yaowu": YaowuSkill(), "fuyong": FuyongSkill()
}