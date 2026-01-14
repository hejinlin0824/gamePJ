import json
import os

# 定义卡牌类型常量
BASIC = "basic"
SCROLL = "scroll"
EQUIP = "equip"
DELAYED = "delayed"

# 技能描述字典 (避免重复文本)
DESCS = {
    "杀": "出牌阶段，对你攻击范围内的一名角色使用。若其不出【闪】，则受到1点伤害。",
    "闪": "抵消一张【杀】。",
    "桃": "出牌阶段，为你恢复1点体力；或有人处于濒死状态时，对其使用，恢复1点体力。",
    "过河拆桥": "出牌阶段，对一名区域里有牌的其他角色使用。你弃置其区域里的一张牌。",
    "顺手牵羊": "出牌阶段，对距离为1的一名区域里有牌的其他角色使用。你获得其区域里的一张牌。",
    "无中生有": "出牌阶段，摸两张牌。",
    "决斗": "出牌阶段，对一名其他角色使用。由其开始，其与你轮流打出一张【杀】，直到有一方不打。不打【杀】的一方受到1点伤害。",
    "借刀杀人": "出牌阶段，对一名装备区里有武器牌的其他角色使用。其需对你指定的一名角色使用一张【杀】，否则将其装备区里的武器牌交给你。",
    "桃园结义": "出牌阶段，所有角色各恢复1点体力。",
    "五谷丰登": "出牌阶段，亮出等同于现存角色数量的牌，每名角色按行动顺序从里面选择并获得一张牌。",
    "南蛮入侵": "出牌阶段，对所有其他角色使用。每名角色需打出一张【杀】，否则受到1点伤害。",
    "万箭齐发": "出牌阶段，对所有其他角色使用。每名角色需打出一张【闪】，否则受到1点伤害。",
    "无懈可击": "抵消一张锦囊牌的效果。",
    "乐不思蜀": "出牌阶段，对一名其他角色使用。判定阶段进行判定：若为红桃，则失效；否则跳过其出牌阶段。",
    "闪电": "出牌阶段，对自己使用。判定阶段进行判定：若为黑桃2~9，则你受到3点雷电伤害；否则将此牌移动到下家的判定区。",
    "诸葛连弩": "锁定技，你使用【杀】无次数限制。",
    "青釭剑": "锁定技，你使用【杀】时，无视目标角色的防具。",
    "雌雄双股剑": "你使用【杀】指定一名异性角色为目标后，你可以令其选择一项：1.弃置一张手牌；2.令你摸一张牌。",
    "寒冰剑": "你使用【杀】造成伤害时，你可以防止此伤害，改为弃置目标角色的两张牌。",
    "贯石斧": "你使用【杀】被【闪】抵消时，你可以弃置两张牌，令此【杀】依然造成伤害。",
    "青龙偃月刀": "你使用【杀】被【闪】抵消时，你可以对相同目标再使用一张【杀】。",
    "丈八蛇矛": "你可以将两张手牌当【杀】使用。",
    "方天画戟": "你使用【杀】时，若你所有的手牌为这张【杀】，此【杀】目标可加二。",
    "麒麟弓": "你使用【杀】造成伤害时，你可以弃置目标角色装备区里的一张坐骑牌。",
    "八卦阵": "每当你需要使用或打出【闪】时，你可以进行判定：若结果为红色，视为你使用或打出了一张【闪】。",
    "仁王盾": "锁定技，黑色【杀】对你无效。",
    "绝影": "锁定技，其他角色计算与你的距离+1。",
    "的卢": "锁定技，其他角色计算与你的距离+1。",
    "爪黄飞电": "锁定技，其他角色计算与你的距离+1。",
    "赤兔": "锁定技，你计算与其他角色的距离-1。",
    "大宛": "锁定技，你计算与其他角色的距离-1。",
    "紫骍": "锁定技，你计算与其他角色的距离-1。",
}

# 完整标准版108张牌数据定义
# 格式: [花色, 点数, 名称, 类型]
raw_data = [
    # === 黑桃 Spade ===
    ["spade", 1, "闪电", DELAYED], ["spade", 2, "雌雄双股剑", EQUIP], 
    ["spade", 2, "八卦阵", EQUIP], ["spade", 3, "过河拆桥", SCROLL],
    ["spade", 4, "过河拆桥", SCROLL], ["spade", 5, "青龙偃月刀", EQUIP], 
    ["spade", 5, "绝影", EQUIP], ["spade", 6, "青釭剑", EQUIP], 
    ["spade", 6, "乐不思蜀", DELAYED], ["spade", 7, "杀", BASIC], 
    ["spade", 7, "南蛮入侵", SCROLL], ["spade", 8, "杀", BASIC], 
    ["spade", 8, "杀", BASIC], ["spade", 9, "杀", BASIC], 
    ["spade", 9, "杀", BASIC], ["spade", 10, "杀", BASIC], 
    ["spade", 10, "杀", BASIC], ["spade", 11, "无懈可击", SCROLL], # J
    ["spade", 11, "顺手牵羊", SCROLL], ["spade", 12, "过河拆桥", SCROLL], # Q
    ["spade", 12, "丈八蛇矛", EQUIP], ["spade", 13, "南蛮入侵", SCROLL], # K
    ["spade", 13, "大宛", EQUIP],

    # === 红桃 Heart ===
    ["heart", 1, "桃园结义", SCROLL], ["heart", 1, "万箭齐发", SCROLL],
    ["heart", 2, "闪", BASIC], ["heart", 2, "闪", BASIC],
    ["heart", 3, "桃", BASIC], ["heart", 3, "五谷丰登", SCROLL],
    ["heart", 4, "桃", BASIC], ["heart", 4, "五谷丰登", SCROLL],
    ["heart", 5, "麒麟弓", EQUIP], ["heart", 5, "赤兔", EQUIP],
    ["heart", 6, "桃", BASIC], ["heart", 6, "乐不思蜀", DELAYED],
    ["heart", 7, "桃", BASIC], ["heart", 7, "无中生有", SCROLL],
    ["heart", 8, "桃", BASIC], ["heart", 8, "无中生有", SCROLL],
    ["heart", 9, "桃", BASIC], ["heart", 9, "无中生有", SCROLL],
    ["heart", 10, "杀", BASIC], ["heart", 10, "杀", BASIC],
    ["heart", 11, "杀", BASIC], ["heart", 11, "无中生有", SCROLL],
    ["heart", 12, "桃", BASIC], ["heart", 12, "过河拆桥", SCROLL],
    ["heart", 12, "闪电", DELAYED], ["heart", 13, "爪黄飞电", EQUIP], # K
    ["heart", 13, "闪", BASIC],

    # === 梅花 Club ===
    ["club", 1, "决斗", SCROLL], ["club", 1, "诸葛连弩", EQUIP],
    ["club", 2, "杀", BASIC], ["club", 2, "八卦阵", EQUIP],
    ["club", 2, "仁王盾", EQUIP], ["club", 3, "杀", BASIC],
    ["club", 3, "过河拆桥", SCROLL], ["club", 4, "杀", BASIC],
    ["club", 4, "过河拆桥", SCROLL], ["club", 5, "杀", BASIC],
    ["club", 5, "的卢", EQUIP], ["club", 6, "杀", BASIC],
    ["club", 6, "乐不思蜀", DELAYED], ["club", 7, "杀", BASIC],
    ["club", 7, "南蛮入侵", SCROLL], ["club", 8, "杀", BASIC],
    ["club", 8, "杀", BASIC], ["club", 9, "杀", BASIC],
    ["club", 9, "杀", BASIC], ["club", 10, "杀", BASIC],
    ["club", 10, "杀", BASIC], ["club", 11, "杀", BASIC],
    ["club", 11, "杀", BASIC], ["club", 12, "借刀杀人", SCROLL],
    ["club", 12, "借刀杀人", SCROLL], ["club", 12, "无懈可击", SCROLL],
    ["club", 13, "借刀杀人", SCROLL], ["club", 13, "无懈可击", SCROLL],

    # === 方片 Diamond ===
    ["diamond", 1, "决斗", SCROLL], ["diamond", 1, "诸葛连弩", EQUIP],
    ["diamond", 2, "闪", BASIC], ["diamond", 2, "闪", BASIC],
    ["diamond", 3, "闪", BASIC], ["diamond", 3, "顺手牵羊", SCROLL],
    ["diamond", 4, "闪", BASIC], ["diamond", 4, "顺手牵羊", SCROLL],
    ["diamond", 5, "闪", BASIC], ["diamond", 5, "贯石斧", EQUIP],
    ["diamond", 6, "闪", BASIC], ["diamond", 6, "杀", BASIC],
    ["diamond", 7, "闪", BASIC], ["diamond", 7, "杀", BASIC],
    ["diamond", 8, "闪", BASIC], ["diamond", 8, "杀", BASIC],
    ["diamond", 9, "闪", BASIC], ["diamond", 9, "杀", BASIC],
    ["diamond", 10, "闪", BASIC], ["diamond", 10, "杀", BASIC],
    ["diamond", 11, "闪", BASIC], ["diamond", 11, "闪", BASIC],
    ["diamond", 12, "桃", BASIC], ["diamond", 12, "方天画戟", EQUIP],
    ["diamond", 12, "无懈可击", SCROLL], ["diamond", 13, "杀", BASIC],
    ["diamond", 13, "紫骍", EQUIP],
]

def generate_json():
    cards_list = []
    
    # 将列表转换为 JSON 对象
    for idx, item in enumerate(raw_data):
        suit, rank, name, ctype = item
        
        # 生成唯一ID (如: sha-spade-7-0)
        # 加 idx 是为了防止同一花色点数有两张牌ID冲突
        card_id = f"{name}-{suit}-{rank}-{idx}"
        
        # 英文转拼音 ID 前缀 (简化)
        # 这里为了演示简单，直接用中文名做ID前缀，实际项目中可用拼音库
        
        card_obj = {
            "card_id": card_id,
            "name": name,
            "suit": suit,
            "rank": rank,
            "type": ctype,
            "description": DESCS.get(name, "暂无描述"),
            "image": f"{name}.jpg" # 预留图片路径
        }
        cards_list.append(card_obj)
    
    # 路径
    output_path = "server/app/game/data/standard_cards.json"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cards_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 成功生成 {len(cards_list)} 张卡牌数据！")
    print(f"📂 文件位置: {output_path}")

if __name__ == "__main__":
    generate_json()