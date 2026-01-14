import json
import random
import os
from typing import List
# 注意这里的导入路径，确保 card.py 在同一目录下
from .card import Card 

class GameDeck:
    def __init__(self):
        self.draw_pile: List[Card] = []  # 摸牌堆
        self.discard_pile: List[Card] = [] # 弃牌堆
        self.init_deck()

    def init_deck(self):
        """从JSON加载卡牌数据"""
        # 获取当前文件所在目录，确保无论在哪启动server都能找到json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "data/standard_cards.json")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                cards_data = json.load(f)
                # 将字典转为 Card 对象
                self.draw_pile = [Card(**data) for data in cards_data]
                self.shuffle() # 加载完顺便洗个牌
                print(f"✅ [GameEngine] 成功加载 {len(self.draw_pile)} 张卡牌")
        except FileNotFoundError:
             print(f"❌ [GameEngine] 错误: 找不到文件 {json_path}")
             # 防止后续报错，初始化为空列表
             self.draw_pile = []
        except Exception as e:
            print(f"❌ [GameEngine] 加载卡牌失败: {e}")
            self.draw_pile = []

    def shuffle(self):
        """洗牌"""
        random.shuffle(self.draw_pile)
        print("🔀 牌堆已洗乱")

    def draw(self, count: int = 1) -> List[Card]:
        """摸牌逻辑"""
        drawn = []
        for _ in range(count):
            # 如果牌堆空了，重洗弃牌堆
            if not self.draw_pile:
                self.recycle_discard_pile()
            
            # 如果还有牌，就摸
            if self.draw_pile:
                drawn.append(self.draw_pile.pop())
        
        return drawn

    def recycle_discard_pile(self):
        """牌堆空了，将弃牌堆洗入摸牌堆"""
        if not self.discard_pile:
            print("⚠️ 牌堆和弃牌堆都空了！无法摸牌")
            return
        
        print("♻️ 弃牌堆重洗...")
        self.draw_pile = self.discard_pile[:]
        self.discard_pile = []
        self.shuffle()

# ==========================================
# ⚠️ 关键点：这一行必须存在！
# main.py 导入的就是这个变量
# ==========================================
game_deck = GameDeck()