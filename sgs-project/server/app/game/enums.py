from enum import Enum

class GamePhase(str, Enum):
    WAITING = "waiting"         # 大厅等待
    PICK_GENERAL = "pick_general" # 选将阶段
    START = "start"             # 游戏初始化
    JUDGE = "judge"             # 判定阶段
    DRAW = "draw"               # 摸牌阶段
    PLAY = "play"               # 出牌阶段
    DISCARD = "discard"         # 弃牌阶段
    FINISH = "finish"           # 回合结束
    GAME_OVER = "game_over"     # 游戏结束

class PendingType(str, Enum):
    """服务器挂起类型：必须等待玩家操作才能继续游戏"""
    ASK_FOR_SHAN = "ask_for_shan"           # 被杀者响应闪
    ASK_FOR_DISMANTLE = "ask_for_dismantle"  # 发起者选牌拆除
    ASK_FOR_SNATCH = "ask_for_snatch"        # 发起者选牌顺走
    
    # 🌟 新增：询问技能发动 (如：黑杀当拆桥，是否发动奇袭？)
    ASK_FOR_SKILL_CONFIRM = "ask_for_skill_confirm"