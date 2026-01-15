from abc import ABC
from typing import TYPE_CHECKING, List
from app.game.card import Card

if TYPE_CHECKING:
    from app.game.room import GameRoom
    from app.game.player import PlayerState

class GeneralSkill(ABC):
    """
    武将技能基类 (策略模式)
    包含各种游戏流程的 '钩子(Hooks)'，引擎在特定时机会调用这些方法
    """
    def __init__(self, name: str):
        self.name = name

    # --- 1. 距离与位置 ---
    def modify_distance(self, room: 'GameRoom', from_player: 'PlayerState', to_player: 'PlayerState', distance: int) -> int:
        """[钩子] 修改计算出的距离 (如：马术)"""
        return distance

    # --- 2. 卡牌转化 ---
    def can_transform_card(self, player: 'PlayerState', card: Card, as_card_name: str) -> bool:
        """[钩子] 转化技：判断手牌 card 是否可以当做 as_card_name 使用 (如：龙胆、武圣)"""
        return False

    # --- 3. 摸牌阶段 (预留) ---
    def modify_draw_count(self, room: 'GameRoom', player: 'PlayerState', count: int) -> int:
        """[钩子] 修改摸牌数量 (如：英姿)"""
        return count

    # --- 4. 攻击限制 (预留) ---
    def has_unlimited_sha(self, player: 'PlayerState') -> bool:
        """[钩子] 是否无限出杀 (如：咆哮)"""
        return False

    # --- 5. 防御判定 (预留) ---
    def can_avoid_target(self, room: 'GameRoom', user: 'PlayerState', target: 'PlayerState', card_name: str) -> bool:
        """[钩子] 是否可以豁免成为目标 (如：空城、谦逊)"""
        return False

# ==========================================
#                 魏国 (Wei)
# ==========================================

class JianxiongSkill(GeneralSkill):
    """【奸雄】：受到伤害后获得牌 (需配合事件系统)"""
    def __init__(self): super().__init__("jianxiong")

class HujiaSkill(GeneralSkill):
    """【护驾】：主公技 (需配合主公系统)"""
    def __init__(self): super().__init__("hujia")

class TianduSkill(GeneralSkill):
    """【天妒】：判定牌生效后获得之 (需配合判定系统)"""
    def __init__(self): super().__init__("tiandu")

class YijiSkill(GeneralSkill):
    """【遗计】：受伤摸两张给别人 (需配合事件系统)"""
    def __init__(self): super().__init__("yiji")

class FankuiSkill(GeneralSkill):
    """【反馈】：受伤抽对方牌 (需配合事件系统)"""
    def __init__(self): super().__init__("fankui")

class GuicaiSkill(GeneralSkill):
    """【鬼才】：改判 (需配合判定系统)"""
    def __init__(self): super().__init__("guicai")

class GanglieSkill(GeneralSkill):
    """【刚烈】：受伤判定反伤 (需配合事件系统)"""
    def __init__(self): super().__init__("ganglie")

class TuxiSkill(GeneralSkill):
    """【突袭】：摸牌阶段抢牌 (需配合阶段重构)"""
    def __init__(self): super().__init__("tuxi")

class LuoyiSkill(GeneralSkill):
    """【裸衣】：少摸牌增伤 (需配合阶段重构)"""
    def __init__(self): super().__init__("luoyi")

class LuoshenSkill(GeneralSkill):
    """【洛神】：回合开始判定拿牌 (需配合阶段重构)"""
    def __init__(self): super().__init__("luoshen")

class QingguoSkill(GeneralSkill):
    """【倾国】：你可以将黑色手牌当【闪】使用或打出。"""
    def __init__(self): super().__init__("qingguo")

    def can_transform_card(self, player: 'PlayerState', card: Card, as_card_name: str) -> bool:
        if as_card_name == "闪":
            # 黑色 (spade/club) 当闪
            if card.suit in ["spade", "club"]:
                return True
        return False

# ==========================================
#                 蜀国 (Shu)
# ==========================================

class RendeSkill(GeneralSkill):
    """【仁德】：给牌加血 (需配合出牌阶段技能按钮)"""
    def __init__(self): super().__init__("rende")

class JijiangSkill(GeneralSkill):
    """【激将】：主公技 (需配合响应系统)"""
    def __init__(self): super().__init__("jijiang")

class WushengSkill(GeneralSkill):
    """【武圣】：你可以将红色手牌当【杀】使用或打出。"""
    def __init__(self): super().__init__("wusheng")

    def can_transform_card(self, player: 'PlayerState', card: Card, as_card_name: str) -> bool:
        if as_card_name == "杀":
            # 红色 (heart/diamond) 当杀
            if card.suit in ["heart", "diamond"]:
                return True
        return False

class PaoxiaoSkill(GeneralSkill):
    """【咆哮】：出杀无限制"""
    def __init__(self): super().__init__("paoxiao")
    
    def has_unlimited_sha(self, player: 'PlayerState') -> bool:
        return True

class GuanxingSkill(GeneralSkill):
    """【观星】：看牌堆顶 (需配合开始阶段)"""
    def __init__(self): super().__init__("guanxing")

class KongchengSkill(GeneralSkill):
    """【空城】：无手牌不能被杀/决斗"""
    def __init__(self): super().__init__("kongcheng")
    
    def can_avoid_target(self, room: 'GameRoom', user: 'PlayerState', target: 'PlayerState', card_name: str) -> bool:
        if not target.hand_cards and card_name in ["杀", "决斗"]:
            return True
        return False

class LongdanSkill(GeneralSkill):
    """【龙胆】：杀当闪，闪当杀。"""
    def __init__(self): super().__init__("longdan")

    def can_transform_card(self, player: 'PlayerState', card: Card, as_card_name: str) -> bool:
        if as_card_name == "杀" and card.name == "闪": return True
        if as_card_name == "闪" and card.name == "杀": return True
        return False

class MashuSkill(GeneralSkill):
    """【马术】：你与其他角色的距离-1。"""
    def __init__(self): super().__init__("mashu")

    def modify_distance(self, room: 'GameRoom', from_player: 'PlayerState', to_player: 'PlayerState', distance: int) -> int:
        # 如果是计算 "我到别人" 的距离 (from_player 是我)
        # 注意：room.get_distance 会遍历 p1.skills
        return max(1, distance - 1)

class TieqiSkill(GeneralSkill):
    """【铁骑】：杀判定强中 (需配合出牌后事件)"""
    def __init__(self): super().__init__("tieqi")

class JizhiSkill(GeneralSkill):
    """【集智】：用锦囊摸牌 (需配合使用牌后事件)"""
    def __init__(self): super().__init__("jizhi")

class QicaiSkill(GeneralSkill):
    """【奇才】：锦囊无距离限制 (目前引擎暂未校验锦囊距离，除顺手牵羊)"""
    def __init__(self): super().__init__("qicai")
    
    def modify_distance(self, room: 'GameRoom', from_player: 'PlayerState', to_player: 'PlayerState', distance: int) -> int:
        # 这里逻辑较复杂，通常是在 card.validate 里判断是否是锦囊，如果是则无视距离
        # 简单实现：暂不处理，因为目前只有顺手牵羊查距离
        return distance

# ==========================================
#                 吴国 (Wu)
# ==========================================

class ZhihengSkill(GeneralSkill):
    """【制衡】：弃牌摸牌 (需配合出牌阶段按钮)"""
    def __init__(self): super().__init__("zhiheng")

class JiuyuanSkill(GeneralSkill):
    """【救援】：主公技"""
    def __init__(self): super().__init__("jiuyuan")

class QixiSkill(GeneralSkill):
    """【奇袭】：黑色牌当【过河拆桥】。"""
    def __init__(self): super().__init__("qixi")

    def can_transform_card(self, player: 'PlayerState', card: Card, as_card_name: str) -> bool:
        if as_card_name == "过河拆桥" and card.suit in ["spade", "club"]:
            return True
        return False

class KejiSkill(GeneralSkill):
    """【克己】：不出杀手牌上限+ (需配合弃牌阶段)"""
    def __init__(self): super().__init__("keji")

class KurouSkill(GeneralSkill):
    """【苦肉】：自残摸牌 (需配合主动技能)"""
    def __init__(self): super().__init__("kurou")

class YingziSkill(GeneralSkill):
    """【英姿】：摸牌阶段多摸一张"""
    def __init__(self): super().__init__("yingzi")
    
    def modify_draw_count(self, room: 'GameRoom', player: 'PlayerState', count: int) -> int:
        return count + 1

class FanjianSkill(GeneralSkill):
    """【反间】：猜花色 (需配合复杂交互)"""
    def __init__(self): super().__init__("fanjian")

class GuoseSkill(GeneralSkill):
    """【国色】：方块牌当【乐不思蜀】。"""
    def __init__(self): super().__init__("guose")

    def can_transform_card(self, player: 'PlayerState', card: Card, as_card_name: str) -> bool:
        if as_card_name == "乐不思蜀" and card.suit == "diamond":
            return True
        return False

class LiuliSkill(GeneralSkill):
    """【流离】：转移杀目标 (需配合响应系统)"""
    def __init__(self): super().__init__("liuli")

class QianxunSkill(GeneralSkill):
    """【谦逊】：不受乐/顺手"""
    def __init__(self): super().__init__("qianxun")
    
    def can_avoid_target(self, room: 'GameRoom', user: 'PlayerState', target: 'PlayerState', card_name: str) -> bool:
        if card_name in ["乐不思蜀", "顺手牵羊"]:
            return True
        return False

class LianyingSkill(GeneralSkill):
    """【连营】：没牌摸牌 (需配合失去牌事件)"""
    def __init__(self): super().__init__("lianying")

class JieyinSkill(GeneralSkill):
    """【结姻】：给牌回血"""
    def __init__(self): super().__init__("jieyin")

class XiaojiSkill(GeneralSkill):
    """【枭姬】：失去装备摸牌"""
    def __init__(self): super().__init__("xiaoji")

# ==========================================
#                 群雄 (Qun)
# ==========================================

class QingnangSkill(GeneralSkill):
    """【青囊】：弃牌回血"""
    def __init__(self): super().__init__("qingnang")

class JijiuSkill(GeneralSkill):
    """【急救】：回合外红色当桃 (需配合濒死事件)"""
    def __init__(self): super().__init__("jijiu")

class WushuangSkill(GeneralSkill):
    """【无双】：杀需两闪，决斗需两杀 (需配合判定逻辑升级)"""
    def __init__(self): super().__init__("wushuang")

class LijianSkill(GeneralSkill):
    """【离间】：强制决斗"""
    def __init__(self): super().__init__("lijian")

class BiyueSkill(GeneralSkill):
    """【闭月】：回合结束摸牌 (需配合结束阶段)"""
    def __init__(self): super().__init__("biyue")

class YongsiSkill(GeneralSkill):
    """【庸肆】：多摸多弃 (需配合阶段重构)"""
    def __init__(self): super().__init__("yongsi")
    
    def modify_draw_count(self, room: 'GameRoom', player: 'PlayerState', count: int) -> int:
        return count + 1 # 简单实现摸牌+1

class WeidiSkill(GeneralSkill):
    """【伪帝】：获主公技"""
    def __init__(self): super().__init__("weidi")

class YaowuSkill(GeneralSkill):
    """【耀武】：负面技"""
    def __init__(self): super().__init__("yaowu")

class FuyongSkill(GeneralSkill):
    """【负勇】：负面技"""
    def __init__(self): super().__init__("fuyong")


# ==========================================
#              技能注册表
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