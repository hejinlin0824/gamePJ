import random
from typing import List
from .card import Card, CardType

class GameDeck:
    def __init__(self):
        self.draw_pile: List[Card] = []      # 摸牌堆
        self.discard_pile: List[Card] = []   # 弃牌堆

    def init_deck(self):
        """
        初始化标准牌堆
        严格按照 Card 模型要求：card_id, name, suit, number, card_type, [distance_limit, attack_range]
        """
        self.draw_pile = []
        self.discard_pile = []
        
        suits = ["spade", "heart", "club", "diamond"]
        
        # --- 1. 生成基本牌 ---
        # 杀 (约 30张)
        for i in range(30):
            suit = suits[i % 4]
            num = (i % 13) + 1
            self.draw_pile.append(Card(
                card_id=f"sha-{i}", name="杀", suit=suit, number=num, 
                card_type=CardType.BASIC
            ))
            
        # 闪 (约 15张)
        for i in range(15):
            suit = suits[i % 2 + 2] # 主要是方块和梅花
            num = (i % 13) + 1
            self.draw_pile.append(Card(
                card_id=f"shan-{i}", name="闪", suit=suit, number=num, 
                card_type=CardType.BASIC
            ))
            
        # 桃 (约 8张)
        for i in range(8):
            suit = "heart"
            num = (i % 5) + 1
            self.draw_pile.append(Card(
                card_id=f"tao-{i}", name="桃", suit=suit, number=num, 
                card_type=CardType.BASIC
            ))

        # --- 2. 生成锦囊牌 ---
        # 无中生有 (4张)
        for i in range(4):
            self.draw_pile.append(Card(
                card_id=f"wuzhong-{i}", name="无中生有", suit="heart", number=7+i, 
                card_type=CardType.STRATEGY
            ))
            
        # 顺手牵羊 (5张, 距离限制1)
        for i in range(5):
            self.draw_pile.append(Card(
                card_id=f"shunshou-{i}", name="顺手牵羊", suit="spade", number=3+i, 
                card_type=CardType.STRATEGY, distance_limit=1
            ))
            
        # 过河拆桥 (6张)
        for i in range(6):
            self.draw_pile.append(Card(
                card_id=f"guohe-{i}", name="过河拆桥", suit="spade", number=3+i, 
                card_type=CardType.STRATEGY
            ))

        # --- 3. 生成装备牌 ---
        # 武器 (各种范围)
        weapons = [
            ("诸葛连弩", 1), ("雌雄双股剑", 2), ("寒冰剑", 2), 
            ("青龙偃月刀", 3), ("丈八蛇矛", 3), ("贯石斧", 3), 
            ("方天画戟", 4), ("麒麟弓", 5)
        ]
        for name, range_val in weapons:
            self.draw_pile.append(Card(
                card_id=f"weapon-{name}", name=name, suit="spade", number=5, 
                card_type=CardType.EQUIP_WEAPON, attack_range=range_val
            ))

        # +1马 (4张)
        for i in range(4):
            self.draw_pile.append(Card(
                card_id=f"plus-horse-{i}", name="+1马", suit="heart", number=5, 
                card_type=CardType.EQUIP_HORSE_PLUS
            ))

        # -1马 (4张)
        for i in range(4):
            self.draw_pile.append(Card(
                card_id=f"minus-horse-{i}", name="-1马", suit="spade", number=5, 
                card_type=CardType.EQUIP_HORSE_MINUS
            ))

        print(f"✅ [GameEngine] 成功加载 {len(self.draw_pile)} 张卡牌")

    def shuffle(self):
        """洗牌"""
        if not self.draw_pile and not self.discard_pile:
            print("⚠️ 牌堆和弃牌堆都空了！无法洗牌")
            return
        random.shuffle(self.draw_pile)
        print("🔀 牌堆已洗乱")

    def draw(self, count: int) -> List[Card]:
        """摸牌逻辑，若摸牌堆空了则将弃牌堆洗入"""
        drawn_cards = []
        for _ in range(count):
            if not self.draw_pile:
                if not self.discard_pile:
                    print("⚠️ 牌堆和弃牌堆都空了！无法摸牌")
                    break
                # 将弃牌堆洗回摸牌堆
                print("♻️ 摸牌堆已空，正在将弃牌堆洗入摸牌堆...")
                self.draw_pile = self.discard_pile[:]
                self.discard_pile = []
                self.shuffle()
            
            if self.draw_pile:
                drawn_cards.append(self.draw_pile.pop())
        return drawn_cards

# 保持单例模式供简单调用，但在 Room 类中我们通常会实例化新的 GameDeck
game_deck = GameDeck()