import json
import os
import random
from typing import List, Optional, Dict, Tuple, Any
from pydantic import BaseModel

from .card import Card, CardType
from .engine import GameDeck
from .enums import GamePhase, PendingType
from .player import Player 

# 引入技能注册表
from .skills.standard import SKILL_REGISTRY
from .skills.general import GENERAL_SKILL_REGISTRY

# === 核心数据模型 ===

class PendingAction(BaseModel):
    """当前正在等待的交互详情"""
    source_sid: str                          # 发起者 (谁出的牌/谁触发的技能)
    target_sid: str                          # 当前需要响应的玩家
    card_id: Optional[str] = None            # 关联卡牌ID (用于前端显示来源)
    action_type: PendingType                 # 响应类型 (出杀/出闪/选牌/技能确认/弃牌...)
    extra_data: Dict[str, Any] = {}          # 复杂上下文 (如五谷的牌堆、AOE的队列、弃牌数量等)

# === 房间逻辑引擎 ===

class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: List[Player] = []
        self.current_player_idx: int = 0
        self.phase: GamePhase = GamePhase.WAITING
        self.is_started: bool = False
        self.deck = GameDeck()
        self.pending_action: Optional[PendingAction] = None
        self.winner_sid: Optional[str] = None 
        
        self.generals_data = self._load_generals()

    def _load_generals(self):
        """读取武将数据"""
        path = os.path.join(os.path.dirname(__file__), "data/generals.json")
        if not os.path.exists(path): return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- 辅助方法 ---
    
    def get_player(self, sid: str) -> Optional[Player]:
        for p in self.players:
            if p.sid == sid: return p
        return None

    def get_next_alive_player(self, current: Player) -> Optional[Player]:
        """获取逆时针的下一位存活玩家"""
        if not self.players: return None
        try:
            idx = self.players.index(current)
        except ValueError:
            return None
            
        count = len(self.players)
        for i in range(1, count):
            p = self.players[(idx + i) % count]
            if p.is_alive: return p
        return None

    # --- 玩家管理 ---

    def add_player(self, sid: str, user_info: dict = None) -> Tuple[bool, str]:
        if self.is_started: return False, "游戏已开始"
        if len(self.players) >= 8: return False, "房间已满"
        if self.get_player(sid): return True, "已在房间内"

        new_username = user_info.get("username", "")
        if new_username:
            for p in self.players:
                if p.username == new_username:
                    return False, "该账号已在房间内"

        is_first = len(self.players) == 0
        
        new_player = Player(
            sid=sid, seat_id=len(self.players) + 1, 
            is_host=is_first, is_ready=is_first,
            username=new_username,
            nickname=user_info.get("nickname", f"群雄{len(self.players) + 1}"),
            avatar=user_info.get("avatar", "default.png")
        )
        self.players.append(new_player)
        return True, "加入成功"

    def remove_player(self, sid: str):
        p = self.get_player(sid)
        if not p: return
        
        if self.is_started and p.is_alive:
            self.handle_disconnect_during_game(sid)
            return

        was_host = p.is_host
        self.players = [pl for pl in self.players if pl.sid != sid]
        
        if was_host and self.players:
            self.players[0].is_host = True
            self.players[0].is_ready = True
            
        for i, pl in enumerate(self.players): pl.seat_id = i + 1

    def kick_player(self, host_sid: str, target_sid: str) -> Tuple[bool, str]:
        host = self.get_player(host_sid)
        if not host or not host.is_host: return False, "权限不足"
        self.remove_player(target_sid)
        return True, "踢出成功"

    def toggle_ready(self, sid: str):
        p = self.get_player(sid)
        if p and not p.is_host: p.is_ready = not p.is_ready
        return True

    # --- 游戏中途退出/死亡逻辑 ---

    def handle_disconnect_during_game(self, sid: str) -> str:
        p = self.get_player(sid)
        if not p or not p.is_alive: return "玩家已死亡或不存在"

        print(f"🏃 {p.nickname} 逃跑，判定死亡")
        
        # 寻找上家 (逆时针最近的存活者) 接收遗产
        my_idx = self.players.index(p)
        receiver = None
        count = len(self.players)
        for i in range(1, count):
            check_idx = (my_idx - i + count) % count
            candidate = self.players[check_idx]
            if candidate.is_alive and candidate.sid != sid:
                receiver = candidate
                break
        
        self.kill_player(p, receiver)
        msg = f"{p.nickname} 逃跑，判定阵亡！"

        # 如果导致游戏结束，直接返回
        if self.phase == GamePhase.GAME_OVER: return msg

        # 清理与该玩家相关的 Pending 状态
        if self.pending_action and self.pending_action.target_sid == sid:
            self.pending_action = None 

        # 如果是当前回合者逃跑，强制结束回合
        current_p = self.players[self.current_player_idx]
        if current_p.sid == sid:
            self.pending_action = None
            next_p = self.get_next_alive_player(p)
            if next_p:
                self._enter_turn_cycle(next_p)
            else:
                self.phase = GamePhase.GAME_OVER

        # 房主转移
        if p.is_host:
            p.is_host = False
            next_host = self.get_next_alive_player(p)
            if next_host: next_host.is_host = True

        return msg

    def kill_player(self, victim: Player, killer: Optional[Player]):
        """执行死亡结算"""
        victim.hp = 0
        victim.is_alive = False
        
        if killer:
            print(f"💀 {victim.nickname} 阵亡，遗产归 {killer.nickname}")
            killer.hand_cards.extend(victim.hand_cards)
            for k, card in victim.equips.items():
                if card: killer.hand_cards.append(card)
        else:
            print(f"💀 {victim.nickname} 阵亡，遗产弃置")
            self.deck.discard_pile.extend(victim.hand_cards)
            for k, card in victim.equips.items():
                if card: self.deck.discard_pile.append(card)
        
        victim.hand_cards = []
        victim.equips = {k: None for k in victim.equips}

        self._check_game_over()

    def _check_game_over(self):
        alive_players = [pl for pl in self.players if pl.is_alive]
        if len(alive_players) <= 1:
            self.phase = GamePhase.GAME_OVER
            self.winner_sid = alive_players[0].sid if alive_players else None

    # --- 属性计算 ---

    def get_distance(self, from_sid: str, to_sid: str) -> int:
        p1, p2 = self.get_player(from_sid), self.get_player(to_sid)
        if not p1 or not p2: return 999
        n = len(self.players)
        if n == 0: return 0
        
        diff = abs(p1.seat_id - p2.seat_id)
        phys_dist = min(diff, n - diff)
        
        plus = 1 if p2.equips["horse_plus"] else 0
        minus = 1 if p1.equips["horse_minus"] else 0
        dist = phys_dist + plus - minus
        
        for s in p1.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s)
            if skill: dist = skill.modify_distance(self, p1, p2, dist)
        
        return max(1, dist)

    def can_attack(self, from_sid: str, to_sid: str) -> bool:
        p = self.get_player(from_sid)
        if not p: return False
        wp = p.equips["weapon"]
        rng = wp.attack_range if wp else 1
        return rng >= self.get_distance(from_sid, to_sid)

    # --- 游戏初始化 ---

    def start_game(self) -> Tuple[bool, str]:
        if len(self.players) < 2: return False, "人数不足2人"
        if not all(p.is_ready for p in self.players): return False, "有玩家未准备"
        if not self.generals_data: return False, "武将数据未加载"

        self.is_started = True
        self.winner_sid = None
        
        g_ids = [g['id'] for g in self.generals_data]
        random.shuffle(g_ids)
        if len(g_ids) < len(self.players) * 3: return False, "武将池不足"

        for p in self.players:
            p.general_id = "" 
            p.skills = []
            p.general_candidates = [g_ids.pop() for _ in range(3)]

        self.phase = GamePhase.PICK_GENERAL
        return True, "进入选将阶段"

    def select_general(self, sid: str, general_id: str) -> Tuple[bool, str]:
        if self.phase != GamePhase.PICK_GENERAL: return False, "非选将阶段"
        p = self.get_player(sid)
        if not p or general_id not in p.general_candidates: return False, "无效选择"
        
        p.general_id = general_id
        if all(pl.general_id for pl in self.players):
            self._finalize_setup()
            return True, "游戏开始！"
        return True, "选将成功"

    def _finalize_setup(self):
        self.deck.init_deck()
        self.deck.shuffle()
        gen_map = {g['id']: g for g in self.generals_data}

        for p in self.players:
            info = gen_map.get(p.general_id)
            if info:
                p.kingdom = info["kingdom"]
                p.max_hp = p.hp = info["max_hp"]
                p.skills = info["skills"]
            p.hand_cards = self.deck.draw(4)
            p.equips = {k: None for k in p.equips}
            p.is_alive = True

        self.current_player_idx = 0
        self._enter_turn_cycle(self.players[0])

    # ==================================================
    # 🌟 核心逻辑：回合循环 (Turn Cycle)
    # ==================================================
    def _enter_turn_cycle(self, player: Player):
        if not player.is_alive:
            nxt = self.get_next_alive_player(player)
            if nxt: self._enter_turn_cycle(nxt)
            return

        self.current_player_idx = self.players.index(player)
        
        # 1. 准备阶段
        self.phase = GamePhase.START
        for s in player.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s)
            if skill: skill.on_phase_start(self, player, "start")

        # 2. 判定阶段
        self.phase = GamePhase.JUDGE
        while player.judging_cards:
            card = player.judging_cards.pop()
            print(f"⚖️ {player.nickname} 判定 {card.name}...")
            
            judge_card = self.deck.draw(1)[0]
            self.deck.discard_pile.append(judge_card)
            print(f"   结果：{judge_card.suit} {judge_card.number}")
            
            # (TODO: 司马懿鬼才改判点，需在此处插入 PendingAction，暂略)

            if card.name == "乐不思蜀":
                if judge_card.suit != "heart":
                    print("❌ 乐不思蜀生效")
                    self.deck.discard_pile.append(card)
                    self.phase = GamePhase.DISCARD
                    self.try_end_turn(player.sid)
                    return
                else:
                    print("✅ 乐不思蜀失效")
                    self.deck.discard_pile.append(card)

            elif card.name == "闪电":
                if judge_card.suit == "spade" and 2 <= judge_card.number <= 9:
                    print("⚡ 闪电劈中！")
                    self.deck.discard_pile.append(card)
                    self.apply_damage(player.sid, 3, source_sid=None, card=card)
                    if not player.is_alive: return 
                else:
                    print("↪️ 闪电移至下家")
                    nxt = self.get_next_alive_player(player)
                    if nxt: nxt.judging_cards.append(card)

        # 3. 摸牌阶段
        self.phase = GamePhase.DRAW
        player.sha_count = 0
        draw_count = 2
        for s in player.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s)
            if skill: draw_count = skill.modify_draw_count(self, player, draw_count)
        player.hand_cards.extend(self.deck.draw(draw_count))
        
        # 4. 出牌阶段
        self.phase = GamePhase.PLAY

    def try_end_turn(self, sid: str) -> Tuple[bool, str]:
        if self.pending_action: return False, "有待处理的操作"
        p = self.get_player(sid)
        if self.players[self.current_player_idx].sid != sid: return False, "非当前回合"

        # 5. 弃牌阶段 (Manual Discard)
        self.phase = GamePhase.DISCARD
        limit = max(0, p.hp)
        for s in p.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s)
            if skill: limit = skill.modify_hand_limit(self, p, limit)

        # 🌟 询问玩家弃牌 (非自动)
        current_hand_count = len(p.hand_cards)
        if current_hand_count > limit:
            diff = current_hand_count - limit
            print(f"📦 {p.nickname} 需要弃置 {diff} 张牌")
            self.pending_action = PendingAction(
                source_sid=sid,
                target_sid=sid,
                action_type=PendingType.ASK_FOR_DISCARD,
                extra_data={"discard_count": diff}
            )
            return True, f"请弃置 {diff} 张牌"
        
        # 不需要弃牌，直接进入结束流程
        return self._proceed_to_finish(p)

    def _proceed_to_finish(self, p: Player) -> Tuple[bool, str]:
        # 6. 结束阶段
        self.phase = GamePhase.FINISH
        for s in p.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s)
            if skill: skill.on_phase_start(self, p, "finish")

        nxt = self.get_next_alive_player(p)
        if nxt:
            self._enter_turn_cycle(nxt)
            return True, "回合结束"
        else:
            self.phase = GamePhase.GAME_OVER
            return True, "游戏结束"

    # ==================================================
    # 🌟 核心逻辑：伤害结算
    # ==================================================
    def apply_damage(self, sid: str, amount: int, source_sid: Optional[str] = None, card: Optional[Card] = None):
        p = self.get_player(sid)
        source = self.get_player(source_sid) if source_sid else None
        if not p or not p.is_alive: return

        p.hp -= amount
        print(f"🩸 {p.nickname} 受到 {amount} 点伤害，剩余 {p.hp}")

        # 触发受伤技能钩子 (如遗计、刚烈)
        for s_name in p.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s_name)
            if skill:
                if skill.on_receive_damage(self, p, source, amount, card):
                    return # 技能中断了结算（如遗计需要等待响应）

        self._resolve_death_state(p, source)

    def _resolve_death_state(self, victim: Player, killer: Optional[Player]):
        if victim.hp <= 0:
            # 简化：直接死亡 (TODO: 濒死求桃)
            self.kill_player(victim, killer)

    # ==================================================
    # 🌟 核心修复：Play Card (出牌)
    # ==================================================
    def play_card(self, sid: str, index: int, target_sid: Optional[str]) -> Tuple[bool, str, Optional[Card]]:
        if self.pending_action or self.phase == GamePhase.GAME_OVER: 
            return False, "禁止操作", None
        
        p = self.get_player(sid)
        if not p or not p.is_alive or self.players[self.current_player_idx].sid != sid: 
            return False, "非当前回合", None
        if index >= len(p.hand_cards): return False, "索引无效", None
        
        card = p.hand_cards[index]
        skill_name = card.name
        can_transform = False

        # --- 技能转化判断 (修复 Bug) ---
        # ⚠️ 仅保留“隐式转化”（无歧义的攻击动作），移除“显式转化”（如奇袭、国色）
        if target_sid:
            for s_name in p.skills:
                skill = GENERAL_SKILL_REGISTRY.get(s_name)
                if not skill: continue
                
                # 武圣：红牌 -> 杀 (无歧义，因为红牌除了桃和装备通常不能主动指定敌人)
                if skill.can_transform_card(p, card, "杀"):
                    skill_name = "杀"; can_transform = True; break
                
                # 龙胆：闪 -> 杀 (无歧义，出牌阶段闪无法打出)
                if skill_name == "闪" and skill.can_transform_card(p, card, "杀"):
                    skill_name = "杀"; can_transform = True; break
                
                # ❌ 移除：奇袭 (黑牌->拆)、国色 (方块->乐)
                # 这些必须走 trigger_active_skill，否则黑杀打不出去，或者想顺手牵羊却变成了拆桥

        # 获取处理器
        if card.card_type.name.startswith("EQUIP"):
            handler = SKILL_REGISTRY["equip_handler"]
        else:
            handler = SKILL_REGISTRY.get(skill_name)

        if not handler: return False, f"未实现卡牌 {skill_name}", None

        # 校验
        ok, msg = handler.validate(self, p, card, target_sid)
        if not ok: return False, msg, None

        # 执行
        ok, msg = handler.execute(self, p, card, target_sid)
        if ok:
            if can_transform: msg = f"(转化) {msg}"
            return True, msg, card
        return False, msg, None

    # ==================================================
    # 🌟 核心新增：Active Skill Trigger (主动技能)
    # ==================================================
    def trigger_active_skill(self, sid: str, skill_name: str, targets: List[str], card_indices: List[int]) -> Tuple[bool, str]:
        """
        处理前端点击按钮触发的技能 (解决奇袭、国色等无法主动发动的问题)
        """
        p = self.get_player(sid)
        if self.phase != GamePhase.PLAY or self.players[self.current_player_idx].sid != sid:
            return False, "非出牌阶段"

        # --- 奇袭 (甘宁)：黑牌当拆 ---
        if skill_name == "qixi":
            if not targets or len(card_indices) != 1: return False, "需选1张牌和1个目标"
            c = p.hand_cards[card_indices[0]]
            if c.suit not in ["spade", "club"]: return False, "必须是黑色牌"
            
            # 消耗牌 (进弃牌堆)
            consumed_card = p.hand_cards.pop(card_indices[0])
            self.deck.discard_pile.append(consumed_card)
            
            # 效果：视为对目标使用过河拆桥
            # 由于拆桥需要交互(选对方的牌)，这里挂起 PendingAction
            target_p = self.get_player(targets[0])
            if not target_p: return False, "目标无效"
            
            self.pending_action = PendingAction(
                source_sid=sid,
                target_sid=sid, # 这里的target是发起者自己，因为需要发起者去点选对方的牌
                action_type=PendingType.ASK_FOR_DISMANTLE,
                extra_data={"target_to_dismantle": target_p.sid}
            )
            return True, f"发动奇袭，请选择要拆卸的牌"

        # --- 国色 (大乔)：方块当乐 ---
        if skill_name == "guose":
            if not targets or len(card_indices) != 1: return False, "需选1张牌和1个目标"
            c = p.hand_cards[card_indices[0]]
            if c.suit != "diamond": return False, "必须是方块牌"
            
            target_p = self.get_player(targets[0])
            if not target_p: return False, "目标无效"
            # 检查判定区是否已有乐
            for jc in target_p.judging_cards:
                if jc.name == "乐不思蜀": return False, "目标已有乐不思蜀"

            # 消耗牌并移入目标判定区
            consumed_card = p.hand_cards.pop(card_indices[0])
            # 变身
            consumed_card.name = "乐不思蜀"
            consumed_card.card_type = CardType.DELAYED # 需确保枚举兼容，或单纯依赖 name 判断
            
            target_p.judging_cards.append(consumed_card)
            return True, f"对 {target_p.nickname} 发动国色 (乐不思蜀)"

        # --- 离间 (貂蝉) ---
        if skill_name == "lijian":
            if len(targets) != 2: return False, "需选择两名男性角色"
            if len(card_indices) != 1: return False, "需弃置一张牌"
            # TODO: 校验男性 (这里暂略，假设全员皆可)
            
            c = p.hand_cards.pop(card_indices[0])
            self.deck.discard_pile.append(c)
            
            # 视为 targets[0] 对 targets[1] 决斗
            self.pending_action = PendingAction(
                source_sid=targets[0],
                target_sid=targets[1],
                action_type=PendingType.ASK_FOR_SHA,
                extra_data={
                    "is_duel": True,
                    "duel_source": targets[0],
                    "duel_target": targets[1]
                }
            )
            return True, f"发动离间！{self.get_player(targets[0]).nickname} 对 {self.get_player(targets[1]).nickname} 决斗"

        # --- 仁德 (刘备) ---
        if skill_name == "rende":
            if not targets or not card_indices: return False, "需选择目标和至少一张牌"
            target_p = self.get_player(targets[0])
            
            cards_to_give = []
            for idx in sorted(card_indices, reverse=True):
                if idx < len(p.hand_cards):
                    cards_to_give.append(p.hand_cards.pop(idx))
            
            target_p.hand_cards.extend(cards_to_give)
            # TODO: 仁德回血逻辑 (记录本回合给牌数量，满2张回1血)
            return True, f"仁德：给了 {target_p.nickname} {len(cards_to_give)} 张牌"

        # --- 青囊 (华佗) ---
        if skill_name == "qingnang":
            if len(card_indices) != 1: return False, "需弃置一张手牌"
            target_id = targets[0] if targets else sid
            target_p = self.get_player(target_id)
            
            if target_p.hp >= target_p.max_hp: return False, "目标体力已满"
            
            c = p.hand_cards.pop(card_indices[0])
            self.deck.discard_pile.append(c)
            
            target_p.hp += 1
            return True, f"发动青囊，{target_p.nickname} 回复1点体力"

        # --- 苦肉 (黄盖) ---
        if skill_name == "kurou":
            p.hp -= 1
            print(f"🩸 {p.nickname} 苦肉失去1点体力")
            if p.hp <= 0:
                self._resolve_death_state(p, None)
                if not p.is_alive: return True, "苦肉自尽"
            
            p.hand_cards.extend(self.deck.draw(2))
            return True, "苦肉：失去1点体力，摸两张牌"

        # --- 制衡 (孙权) ---
        if skill_name == "zhiheng":
            if not card_indices: return False, "至少弃置一张牌"
            count = len(card_indices)
            for idx in sorted(card_indices, reverse=True):
                if idx < len(p.hand_cards):
                    self.deck.discard_pile.append(p.hand_cards.pop(idx))
            
            p.hand_cards.extend(self.deck.draw(count))
            return True, f"制衡：重铸了 {count} 张牌"
            
        # --- 结姻 (孙尚香) ---
        if skill_name == "jieyin":
            if len(card_indices) != 2: return False, "需弃置两张手牌"
            if len(targets) != 1: return False, "需选择一名男性角色"
            target_p = self.get_player(targets[0])
            
            if p.hp >= p.max_hp and target_p.hp >= target_p.max_hp:
                return False, "双方体力均已满" # 至少一人受伤才可发动(规则细则略有不同，简化处理)

            for idx in sorted(card_indices, reverse=True):
                self.deck.discard_pile.append(p.hand_cards.pop(idx))
            
            if p.hp < p.max_hp: p.hp += 1
            if target_p.hp < target_p.max_hp: target_p.hp += 1
            return True, f"结姻：与 {target_p.nickname} 各回复1点体力"

        # --- 反间 (周瑜) ---
        if skill_name == "fanjian":
            # 反间交互极其复杂(猜花色)，这里做简化版：直接令对方弃牌或扣血
            # 完整版需要 PendingType.ASK_FOR_FANJIAN
            if len(targets) != 1: return False, "需选择一名目标"
            target_p = self.get_player(targets[0])
            # 简化：对方直接流失1点体力 (TODO: 实现猜花色交互)
            target_p.hp -= 1
            return True, f"反间(简化)：{target_p.nickname} 受到折磨"

        return False, "技能未实现或条件不符"

    # ==================================================
    # 🌟 核心逻辑：响应处理器
    # ==================================================
    def handle_response(self, sid: str, card_index: Optional[int], target_area: Optional[str] = None, extra_payload: dict = None) -> Tuple[bool, str]:
        if not self.pending_action or self.pending_action.target_sid != sid:
            return False, "无需响应"
            
        act = self.pending_action
        p = self.get_player(sid)

        # --- 手动弃牌 (ASK_FOR_DISCARD) ---
        if act.action_type == PendingType.ASK_FOR_DISCARD:
            if not extra_payload or "indices" not in extra_payload:
                return False, "请选择要弃置的牌"
            
            indices = sorted(extra_payload["indices"], reverse=True)
            required_count = act.extra_data["discard_count"]
            
            if len(indices) != required_count:
                return False, f"数量错误，需弃 {required_count} 张"
            
            discarded_names = []
            for idx in indices:
                if idx < len(p.hand_cards):
                    c = p.hand_cards.pop(idx)
                    self.deck.discard_pile.append(c)
                    discarded_names.append(c.name)
            
            self.pending_action = None
            self._proceed_to_finish(p)
            return True, f"弃置了 {','.join(discarded_names)}"

        # --- 奇袭/拆桥后续 (ASK_FOR_DISMANTLE) ---
        if act.action_type == PendingType.ASK_FOR_DISMANTLE:
            target_p = self.get_player(act.extra_data["target_to_dismantle"])
            if not target_p: return False, "目标丢失"
            # target_area 由前端传回: 'hand', 'weapon', 'armor', 'horse_plus', 'horse_minus'
            self._move_card_response(target_p, p, target_area, to_hand=False) # 拆：进弃牌堆
            self.pending_action = None
            return True, "拆除成功"

        # --- 顺手牵羊后续 (ASK_FOR_SNATCH) ---
        if act.action_type == PendingType.ASK_FOR_SNATCH:
            target_p = self.get_player(act.extra_data["target_to_snatch"])
            if not target_p: return False, "目标丢失"
            self._move_card_response(target_p, p, target_area, to_hand=True) # 顺：进手牌
            self.pending_action = None
            return True, "顺手牵羊成功"

        # --- 五谷丰登 (ASK_FOR_CHOOSE_CARD) ---
        if act.action_type == PendingType.ASK_FOR_CHOOSE_CARD:
            if card_index is None: return False, "必须选牌"
            wugu_cards = act.extra_data["wugu_cards"]
            if card_index >= len(wugu_cards): return False, "无效选择"
            
            # 拿牌
            c_data = wugu_cards.pop(card_index)
            chosen = Card(**c_data)
            p.hand_cards.append(chosen)
            
            # 轮转
            targets = act.extra_data["aoe_targets"]
            next_idx = act.extra_data["current_index"] + 1
            if next_idx < len(targets) and wugu_cards:
                act.target_sid = targets[next_idx]
                act.extra_data["current_index"] = next_idx
                return True, f"获得了 {chosen.name}"
            else:
                # 剩余进弃牌
                for d in wugu_cards: self.deck.discard_pile.append(Card(**d))
                self.pending_action = None
                return True, "五谷丰登结束"

        # --- 决斗/南蛮/万箭 (ASK_FOR_SHA / SHAN) ---
        # 1. 响应【杀】(决斗/南蛮)
        if act.action_type == PendingType.ASK_FOR_SHA:
            is_duel = act.extra_data.get("is_duel", False)
            if card_index is not None:
                c = p.hand_cards[card_index]
                if c.name == "杀": # 暂不处理转化
                    p.hand_cards.pop(card_index)
                    self.deck.discard_pile.append(c)
                    if is_duel:
                        # 决斗：踢皮球
                        opp = act.extra_data["duel_source"] if sid == act.extra_data["duel_target"] else act.extra_data["duel_target"]
                        act.target_sid = opp
                        return True, "打出【杀】"
                    else:
                        # 南蛮：下一位
                        return self._next_aoe_target(p)
            
            # 放弃
            if is_duel:
                self.pending_action = None
                src = act.extra_data["duel_source"] if sid == act.extra_data["duel_target"] else act.extra_data["duel_target"]
                self.apply_damage(sid, 1, source_sid=src)
                return True, "决斗失败，受到伤害"
            else:
                return self._fail_aoe_response(p, act)

        # 2. 响应【闪】(普通杀/万箭)
        if act.action_type == PendingType.ASK_FOR_SHAN:
            is_aoe = "aoe_targets" in act.extra_data
            if card_index is not None:
                c = p.hand_cards[card_index]
                is_valid = (c.name == "闪")
                # 倾国检查
                if not is_valid:
                    for s in p.skills:
                        skill = GENERAL_SKILL_REGISTRY.get(s)
                        if skill and skill.can_transform_card(p, c, "闪"): is_valid = True; break
                
                if is_valid:
                    p.hand_cards.pop(card_index)
                    self.deck.discard_pile.append(c)
                    if is_aoe: return self._next_aoe_target(p)
                    else:
                        self.pending_action = None
                        return True, "出闪抵消"
            
            # 放弃
            if is_aoe: return self._fail_aoe_response(p, act)
            else:
                self.pending_action = None
                self.apply_damage(sid, 1, source_sid=act.source_sid)
                return True, "受到伤害"

        # --- 遗计 (ASK_FOR_YIJI) ---
        if act.action_type == PendingType.ASK_FOR_YIJI:
            if extra_payload:
                target_p = self.get_player(extra_payload.get("target_id"))
                cid = extra_payload.get("card_id")
                found = next((c for c in p.hand_cards if c.card_id == cid), None)
                
                if target_p and found:
                    p.hand_cards.remove(found)
                    target_p.hand_cards.append(found)
                    self.pending_action = None
                    self._resolve_death_state(p, None)
                    return True, f"分牌给 {target_p.nickname}"
            
            self.pending_action = None
            self._resolve_death_state(p, None)
            return True, "结束遗计"

        # --- 刚烈 (ASK_FOR_GANGLIE) ---
        if act.action_type == PendingType.ASK_FOR_GANGLIE:
            self.pending_action = None
            if target_area == "confirm":
                src = act.extra_data["source_sid"]
                self.apply_damage(src, 1, source_sid=sid)
                return True, "刚烈生效"
            return True, "放弃刚烈"

        # --- 借刀 (ASK_FOR_COLLATERAL) ---
        if act.action_type == PendingType.ASK_FOR_COLLATERAL:
            wp = p.equips.get("weapon")
            if wp:
                p.equips["weapon"] = None
                src = self.get_player(act.source_sid)
                if src: src.hand_cards.append(wp)
                self.pending_action = None
                return True, "交出武器"
            self.pending_action = None
            return True, "无武器可交"

        return False, "未知响应"

    # --- 辅助逻辑 (移动牌/AOE轮转) ---
    
    def _move_card_response(self, from_p: Player, to_p: Player, area: str, to_hand: bool):
        card = None
        if area == "hand" and from_p.hand_cards:
            idx = random.randint(0, len(from_p.hand_cards)-1)
            card = from_p.hand_cards.pop(idx)
        elif area in from_p.equips:
            card = from_p.equips[area]
            if card: from_p.equips[area] = None
        
        if card:
            if to_hand: to_p.hand_cards.append(card)
            else: self.deck.discard_pile.append(card)

    def _next_aoe_target(self, current_p: Player) -> Tuple[bool, str]:
        act = self.pending_action
        targets = act.extra_data["aoe_targets"]
        curr_idx = act.extra_data["current_index"]
        next_idx = curr_idx + 1
        
        if next_idx >= len(targets):
            self.pending_action = None
            return True, "锦囊结算完毕"
        
        act.target_sid = targets[next_idx]
        act.extra_data["current_index"] = next_idx
        return True, "轮到下一位响应"

    def _fail_aoe_response(self, p: Player, act: PendingAction) -> Tuple[bool, str]:
        saved_data = act.extra_data.copy()
        saved_source = act.source_sid
        saved_type = act.action_type
        
        self.pending_action = None
        self.apply_damage(p.sid, 1, source_sid=saved_source)
        
        if not self.pending_action and p.is_alive:
            # 恢复AOE
            targets = saved_data["aoe_targets"]
            curr_idx = saved_data["current_index"]
            next_idx = curr_idx + 1
            if next_idx < len(targets):
                self.pending_action = PendingAction(
                    source_sid=saved_source,
                    target_sid=targets[next_idx],
                    action_type=saved_type,
                    extra_data=saved_data
                )
                self.pending_action.extra_data["current_index"] = next_idx
                return True, "轮转下一位"
            else:
                return True, "结算完毕"
        return True, "受到伤害"

    def get_public_state(self):
        return {
            "room_id": self.room_id, "phase": self.phase, 
            "current_seat": self.players[self.current_player_idx].seat_id if self.players else 0,
            "is_started": self.is_started, "deck_count": len(self.deck.draw_pile),
            "pending": self.pending_action.model_dump() if self.pending_action else None,
            "winner_sid": self.winner_sid,
            "players": [
                {
                    "sid": p.sid, "seat_id": p.seat_id, "hp": p.hp, "max_hp": p.max_hp,
                    "nickname": p.nickname, "avatar": p.avatar, "general_id": p.general_id,
                    "kingdom": p.kingdom, "is_alive": p.is_alive, "is_ready": p.is_ready, "is_host": p.is_host,
                    "card_count": len(p.hand_cards),
                    "equips": {k: (v.name if v else None) for k, v in p.equips.items()},
                    "sha_count": p.sha_count,
                    "skills": p.skills,
                    "candidates": p.general_candidates if self.phase == GamePhase.PICK_GENERAL else []
                } for p in self.players
            ]
        }