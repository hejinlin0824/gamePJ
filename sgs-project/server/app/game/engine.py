import random
from typing import List, Optional
from .card import Card, CardType

class GameDeck:
    def __init__(self):
        self.draw_pile: List[Card] = []    # 摸牌堆
        self.discard_pile: List[Card] = [] # 弃牌堆

    def init_deck(self):
        """
        初始化标准版三国杀牌堆 (共108张)
        包含：基本牌、锦囊牌、装备牌
        数据来源：三国杀标准版卡牌列表
        """
        self.draw_pile = []
        self.discard_pile = []
        cards_data = []

        # ==========================================
        # 1. 装备牌 (Weapons, Armors, Horses)
        # ==========================================
        
        # --- 武器 (Attack Range) ---
        # 诸葛连弩 (Range: 1) - 梅花1, 方块1
        cards_data.append(("诸葛连弩", "club", 1, CardType.EQUIP_WEAPON, 1))
        cards_data.append(("诸葛连弩", "diamond", 1, CardType.EQUIP_WEAPON, 1))
        
        # 雌雄双股剑 (Range: 2) - 黑桃2
        cards_data.append(("雌雄双股剑", "spade", 2, CardType.EQUIP_WEAPON, 2))
        
        # 青釭剑 (Range: 2) - 黑桃6
        cards_data.append(("青釭剑", "spade", 6, CardType.EQUIP_WEAPON, 2))
        
        # 寒冰剑 (Range: 2) - 黑桃2 (注: 标准版通常替代八卦，但在某些版本共存，这里按标准版处理，替换一张八卦或作为额外)
        # 标准版卡表：黑桃2是八卦阵，梅花2是八卦阵。寒冰剑通常在EX包。
        # 这里为了游戏性，我们将黑桃2定为雌雄双股剑(上文已加)，这里修正标准版配置：
        # 严格标准版：
        # 诸葛连弩x2, 雌雄双股剑x1, 青釭剑x1, 青龙偃月刀x1, 丈八蛇矛x1, 贯石斧x1, 方天画戟x1, 麒麟弓x1, 寒冰剑x1(EX), 仁王盾(EX)...
        # 既然要完整体验，我们加入标准版+EX包的常用装备。
        
        cards_data.append(("寒冰剑", "spade", 2, CardType.EQUIP_WEAPON, 2)) # 占位
        cards_data.append(("青龙偃月刀", "spade", 5, CardType.EQUIP_WEAPON, 3))
        cards_data.append(("丈八蛇矛", "spade", 12, CardType.EQUIP_WEAPON, 3))
        cards_data.append(("贯石斧", "diamond", 5, CardType.EQUIP_WEAPON, 3))
        cards_data.append(("方天画戟", "diamond", 12, CardType.EQUIP_WEAPON, 4))
        cards_data.append(("麒麟弓", "heart", 5, CardType.EQUIP_WEAPON, 5))
        cards_data.append(("朱雀羽扇", "diamond", 1, CardType.EQUIP_WEAPON, 4)) # EX
        cards_data.append(("古锭刀", "spade", 1, CardType.EQUIP_WEAPON, 2))   # EX

        # --- 防具 (Armor) ---
        cards_data.append(("八卦阵", "spade", 2, CardType.EQUIP_ARMOR, 0))
        cards_data.append(("八卦阵", "club", 2, CardType.EQUIP_ARMOR, 0))
        cards_data.append(("仁王盾", "club", 2, CardType.EQUIP_ARMOR, 0))
        cards_data.append(("藤甲", "spade", 2, CardType.EQUIP_ARMOR, 0))      # EX
        cards_data.append(("藤甲", "club", 2, CardType.EQUIP_ARMOR, 0))       # EX
        cards_data.append(("白银狮子", "club", 1, CardType.EQUIP_ARMOR, 0))   # EX

        # --- 进攻马 (-1 Horse) ---
        cards_data.append(("赤兔", "heart", 5, CardType.EQUIP_HORSE_MINUS, 0))
        cards_data.append(("大宛", "spade", 13, CardType.EQUIP_HORSE_MINUS, 0))
        cards_data.append(("紫骍", "diamond", 13, CardType.EQUIP_HORSE_MINUS, 0))

        # --- 防御马 (+1 Horse) ---
        cards_data.append(("绝影", "spade", 5, CardType.EQUIP_HORSE_PLUS, 0))
        cards_data.append(("的卢", "club", 5, CardType.EQUIP_HORSE_PLUS, 0))
        cards_data.append(("爪黄飞电", "heart", 13, CardType.EQUIP_HORSE_PLUS, 0))
        cards_data.append(("骅骝", "diamond", 13, CardType.EQUIP_HORSE_PLUS, 0)) # EX

        # ==========================================
        # 2. 基本牌 (Basic Cards)
        # ==========================================
        
        # --- 杀 (Slash) : 共30张 ---
        # 黑桃杀 (7张)
        for num in [7, 8, 8, 9, 9, 10, 10]:
            cards_data.append(("杀", "spade", num, CardType.BASIC, 0))
        # 红桃杀 (3张)
        for num in [10, 10, 11]:
            cards_data.append(("杀", "heart", num, CardType.BASIC, 0))
        # 梅花杀 (14张)
        for num in [2, 3, 4, 5, 6, 7, 8, 8, 9, 9, 10, 10, 11, 11]:
            cards_data.append(("杀", "club", num, CardType.BASIC, 0))
        # 方块杀 (6张)
        for num in [6, 7, 8, 9, 10, 13]:
            cards_data.append(("杀", "diamond", num, CardType.BASIC, 0))

        # --- 闪 (Dodge) : 共15张 ---
        # 红桃闪 (3张 - 含修正)
        for num in [2, 2, 13]:
            cards_data.append(("闪", "heart", num, CardType.BASIC, 0))
        # 方块闪 (12张)
        for num in [2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11]:
            cards_data.append(("闪", "diamond", num, CardType.BASIC, 0))

        # --- 桃 (Peach) : 共8张 ---
        # 红桃桃 (7张)
        for num in [3, 4, 6, 7, 8, 9, 12]:
            cards_data.append(("桃", "heart", num, CardType.BASIC, 0))
        # 方块桃 (1张)
        cards_data.append(("桃", "diamond", 12, CardType.BASIC, 0))
        
        # 酒 (EX) - 既然我们要完整体验，加几张酒
        cards_data.append(("酒", "diamond", 9, CardType.BASIC, 0))
        cards_data.append(("酒", "spade", 3, CardType.BASIC, 0))
        cards_data.append(("酒", "club", 9, CardType.BASIC, 0))

        # ==========================================
        # 3. 锦囊牌 (Scrolls / Strategy)
        # ==========================================

        # --- 非延时锦囊 ---
        
        # 决斗 (Duel) - 3张
        cards_data.append(("决斗", "spade", 1, CardType.STRATEGY, 0))
        cards_data.append(("决斗", "club", 1, CardType.STRATEGY, 0))
        cards_data.append(("决斗", "diamond", 1, CardType.STRATEGY, 0))
        
        # 过河拆桥 (Dismantle) - 6张
        cards_data.append(("过河拆桥", "spade", 3, CardType.STRATEGY, 0))
        cards_data.append(("过河拆桥", "spade", 4, CardType.STRATEGY, 0))
        cards_data.append(("过河拆桥", "spade", 12, CardType.STRATEGY, 0))
        cards_data.append(("过河拆桥", "heart", 12, CardType.STRATEGY, 0))
        cards_data.append(("过河拆桥", "club", 3, CardType.STRATEGY, 0))
        cards_data.append(("过河拆桥", "club", 4, CardType.STRATEGY, 0))
        
        # 顺手牵羊 (Snatch) - 5张 (距离限制 1)
        cards_data.append(("顺手牵羊", "spade", 3, CardType.STRATEGY, 1))
        cards_data.append(("顺手牵羊", "spade", 4, CardType.STRATEGY, 1))
        cards_data.append(("顺手牵羊", "spade", 11, CardType.STRATEGY, 1))
        cards_data.append(("顺手牵羊", "diamond", 3, CardType.STRATEGY, 1))
        cards_data.append(("顺手牵羊", "diamond", 4, CardType.STRATEGY, 1))
        
        # 无中生有 (Something From Nothing) - 4张
        cards_data.append(("无中生有", "heart", 7, CardType.STRATEGY, 0))
        cards_data.append(("无中生有", "heart", 8, CardType.STRATEGY, 0))
        cards_data.append(("无中生有", "heart", 9, CardType.STRATEGY, 0))
        cards_data.append(("无中生有", "heart", 11, CardType.STRATEGY, 0))
        
        # 南蛮入侵 (Barbarian Invasion) - 3张
        cards_data.append(("南蛮入侵", "spade", 7, CardType.STRATEGY, 0))
        cards_data.append(("南蛮入侵", "spade", 13, CardType.STRATEGY, 0))
        cards_data.append(("南蛮入侵", "club", 7, CardType.STRATEGY, 0))
        
        # 万箭齐发 (Archery Attack) - 1张
        cards_data.append(("万箭齐发", "heart", 1, CardType.STRATEGY, 0))
        
        # 桃园结义 (Peach Garden) - 1张
        cards_data.append(("桃园结义", "heart", 1, CardType.STRATEGY, 0))
        
        # 五谷丰登 (Harvest) - 2张
        cards_data.append(("五谷丰登", "heart", 3, CardType.STRATEGY, 0))
        cards_data.append(("五谷丰登", "heart", 4, CardType.STRATEGY, 0))
        
        # 借刀杀人 (Collateral) - 2张
        cards_data.append(("借刀杀人", "club", 12, CardType.STRATEGY, 0))
        cards_data.append(("借刀杀人", "club", 13, CardType.STRATEGY, 0))
        
        # 无懈可击 (Nullification) - 4张 (有的版本是3张，这里给足4张)
        cards_data.append(("无懈可击", "spade", 11, CardType.STRATEGY, 0))
        cards_data.append(("无懈可击", "club", 12, CardType.STRATEGY, 0))
        cards_data.append(("无懈可击", "club", 13, CardType.STRATEGY, 0))
        cards_data.append(("无懈可击", "diamond", 12, CardType.STRATEGY, 0))
        
        # 火攻 (Fire Attack) - EX
        cards_data.append(("火攻", "heart", 2, CardType.STRATEGY, 0))
        cards_data.append(("火攻", "heart", 3, CardType.STRATEGY, 0))
        cards_data.append(("火攻", "diamond", 12, CardType.STRATEGY, 0))

        # --- 延时锦囊 (Delayed) ---
        
        # 乐不思蜀 (Indulgence) - 3张
        cards_data.append(("乐不思蜀", "spade", 6, "delayed", 0)) # 注意类型是 delayed
        cards_data.append(("乐不思蜀", "heart", 6, "delayed", 0))
        cards_data.append(("乐不思蜀", "club", 6, "delayed", 0))
        
        # 闪电 (Lightning) - 1张
        cards_data.append(("闪电", "spade", 1, "delayed", 0))
        
        # 兵粮寸断 (Supply Shortage) - EX
        cards_data.append(("兵粮寸断", "spade", 10, "delayed", 1)) # 距离限制1
        cards_data.append(("兵粮寸断", "club", 4, "delayed", 1))

        # ==========================================
        # 生成 Card 对象
        # ==========================================
        for idx, (name, suit, num, c_type, dist) in enumerate(cards_data):
            # 处理 CardType 枚举兼容性 (如果传入的是字符串 'delayed'，需处理)
            final_type = c_type
            if c_type == "delayed":
                # 假设 CardType 枚举中可能没有 DELAYED，我们用 STRATEGY + 标记，或者扩展 CardType
                # 这里为了兼容性，假设 card.py 已经定义了 CardType.DELAYED，如果没有，请在 card.py 添加
                # 或者复用 STRATEGY，但 name 区分
                try:
                    final_type = CardType.DELAYED
                except AttributeError:
                    final_type = CardType.STRATEGY # 回退方案
            
            # 武器攻击范围 (只有装备牌有)
            rng = dist if c_type == CardType.EQUIP_WEAPON else 0
            
            # 锦囊距离限制 (顺手牵羊、兵粮寸断)
            limit = dist if name in ["顺手牵羊", "兵粮寸断"] else 0

            card = Card(
                card_id=f"{name}-{suit}-{num}-{idx}", # 唯一ID
                name=name,
                suit=suit,
                number=num,
                card_type=final_type,
                attack_range=rng,
                distance_limit=limit
            )
            self.draw_pile.append(card)

        print(f"✅ [GameEngine] 完整牌堆初始化完毕，共 {len(self.draw_pile)} 张卡牌 (含标准版+EX)")

    def shuffle(self):
        """洗牌：打乱摸牌堆"""
        if not self.draw_pile:
            print("⚠️ 牌堆为空，无法洗牌")
            return
        random.shuffle(self.draw_pile)
        print("🔀 牌堆已洗乱")

    def draw(self, count: int) -> List[Card]:
        """
        摸牌逻辑
        如果摸牌堆不够，自动将弃牌堆洗回摸牌堆
        """
        drawn_cards = []
        for _ in range(count):
            if not self.draw_pile:
                print("♻️ 摸牌堆已空，正在重洗弃牌堆...")
                if not self.discard_pile:
                    print("⚠️ 警告：所有牌都被摸光了！游戏进入卡死状态（极其罕见）")
                    break
                
                # 将弃牌堆洗回摸牌堆
                self.draw_pile = self.discard_pile[:]
                self.discard_pile = []
                self.shuffle()
            
            if self.draw_pile:
                drawn_cards.append(self.draw_pile.pop())
                
        return drawn_cards

# 全局单例 (可选)
game_deck = GameDeck()