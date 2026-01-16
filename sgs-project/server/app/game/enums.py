from enum import Enum

class GamePhase(str, Enum):
    """游戏阶段枚举"""
    WAITING = "waiting"          # 大厅等待
    PICK_GENERAL = "pick_general"# 选将阶段
    START = "start"              # 回合开始 (洛神、观星)
    JUDGE = "judge"              # 判定阶段 (乐不思蜀、闪电)
    DRAW = "draw"                # 摸牌阶段
    PLAY = "play"                # 出牌阶段
    DISCARD = "discard"          # 弃牌阶段
    FINISH = "finish"            # 回合结束 (闭月)
    GAME_OVER = "game_over"      # 游戏结束

class PendingType(str, Enum):
    """
    服务器挂起状态枚举：定义了前端此时应该展示什么弹窗或进入什么交互模式
    """
    # === 1. 基础卡牌响应 ===
    ASK_FOR_SHAN = "ask_for_shan"           # 杀 -> 请出闪 / 万箭齐发 -> 请出闪
    ASK_FOR_SHA = "ask_for_sha"             # 决斗/南蛮入侵 -> 请出杀
    ASK_FOR_PEACH = "ask_for_peach"         # 濒死 -> 请出桃
    ASK_FOR_WUXIE = "ask_for_wuxie"         # 锦囊生效前 -> 请出无懈可击

    # === 2. 交互类卡牌响应 ===
    ASK_FOR_DISMANTLE = "ask_for_dismantle" # 过河拆桥：选择弃置对方一张牌
    ASK_FOR_SNATCH = "ask_for_snatch"       # 顺手牵羊：获得对方一张牌
    ASK_FOR_COLLATERAL = "ask_for_collateral" # 借刀杀人：出杀或交刀
    ASK_FOR_CHOOSE_CARD = "ask_for_choose_card" # 五谷丰登：从公用牌堆选一张

    # === 3. 核心流程交互 ===
    ASK_FOR_DISCARD = "ask_for_discard"     # 弃牌阶段：请弃置 X 张手牌 (支持多选)

    # === 4. 技能交互响应 ===
    ASK_FOR_SKILL_CONFIRM = "ask_for_skill_confirm" # 主动/被动技确认 (如：是否发动奸雄？是否发动奇袭？)

    # === 5. 魏国武将技能 ===
    ASK_FOR_YIJI = "ask_for_yiji"           # 郭嘉【遗计】：分配获得的牌
    ASK_FOR_GANGLIE = "ask_for_ganglie"     # 夏侯惇【刚烈】：判红桃失败后 -> 弃牌或掉血
    ASK_FOR_GUICAI = "ask_for_guicai"       # 司马懿【鬼才】：打出一张手牌代替判定牌

    # === 6. 蜀国武将技能 ===
    ASK_FOR_GUANXING = "ask_for_guanxing"   # 诸葛亮【观星】：调整牌堆顶顺序

    # === 7. 吴国武将技能 ===
    ASK_FOR_FANJIAN = "ask_for_fanjian"     # 周瑜【反间】：猜花色
    ASK_FOR_LIULI = "ask_for_liuli"         # 大乔【流离】：弃牌转移杀的目标

    # === 8. 群雄武将技能 ===
    ASK_FOR_LIJIAN = "ask_for_lijian"       # 貂蝉【离间】：(通常是主动技触发，若需响应则是被离间者出杀，走 ASK_FOR_SHA)