import json
import os
import random
from typing import List, Optional, Dict, Tuple, Any
from pydantic import BaseModel

from .card import Card, CardType
from .engine import GameDeck
from .enums import GamePhase, PendingType
from .player import Player 

from .skills.standard import SKILL_REGISTRY
from .skills.general import GENERAL_SKILL_REGISTRY

# === 核心数据模型 ===

class PendingAction(BaseModel):
    """当前正在等待的交互详情"""
    source_sid: str                       
    target_sid: str                       
    card_id: Optional[str] = None            
    action_type: PendingType                 
    extra_data: Dict[str, Any] = {}          

# === 房间逻辑引擎核心 ===

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
        """读取 JSON 文件"""
        path = os.path.join(os.path.dirname(__file__), "data/generals.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- 基础管理 ---

    def get_player(self, sid: str) -> Optional[Player]:
        for p in self.players:
            if p.sid == sid: return p
        return None

    def add_player(self, sid: str, user_info: dict = None) -> Tuple[bool, str]:
        if self.is_started: return False, "游戏已开始"
        if len(self.players) >= 8: return False, "房间已满"
        if self.get_player(sid): return True, "已在房间内"

        # 🌟 修复：禁止同一账号重复加入
        new_username = user_info.get("username", "")
        if new_username:
            for p in self.players:
                if p.username == new_username:
                    return False, "该账号已在房间内，禁止重复加入"

        is_first = len(self.players) == 0
        
        new_player = Player(
            sid=sid, 
            seat_id=len(self.players) + 1, 
            is_host=is_first, 
            is_ready=is_first,
            username=new_username,
            nickname=user_info.get("nickname", f"群雄{len(self.players) + 1}"),
            avatar=user_info.get("avatar", "default.png")
        )
        self.players.append(new_player)
        return True, "加入成功"

    def remove_player(self, sid: str):
        p = self.get_player(sid)
        if not p: return
        
        # 🌟 游戏进行中离开 -> 走逃跑逻辑
        if self.is_started and p.is_alive:
            self.handle_disconnect_during_game(sid)
            return

        # 游戏未开始/已结束 -> 正常移除
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

    # --- 🌟 游戏中途退出与死亡逻辑 (Fix Deadlock) ---

    def handle_disconnect_during_game(self, sid: str) -> str:
        p = self.get_player(sid)
        if not p or not p.is_alive: return "玩家已死亡或不存在"

        print(f"🏃 玩家 {p.nickname} 中途逃跑，判定死亡")
        
        my_idx = self.players.index(p)
        receiver = None
        count = len(self.players)
        
        # 1. 寻找上家 (逆时针寻找第一个存活者)
        for i in range(1, count):
            check_idx = (my_idx - i + count) % count
            candidate = self.players[check_idx]
            if candidate.is_alive and candidate.sid != sid:
                receiver = candidate
                break
        
        # 2. 死亡结算
        self.kill_player(p, receiver)
        msg = f"{p.nickname} 临阵脱逃，全军覆没！"
        if receiver:
            msg += f" 其辎重被上家 {receiver.nickname} 接收。"
        else:
            msg += " 辎重尽数弃置。"

        # 3. 胜负检测优先
        if self.phase == GamePhase.GAME_OVER:
            print("🏆 逃跑导致游戏结束")
            return msg

        # 🌟 4. 状态清理与回合强制结束
        
        # A. 如果有人正在对他进行操作 (Pending Target 是逃跑者) -> 强制取消
        if self.pending_action and self.pending_action.target_sid == sid:
            print("⚠️ 逃跑者有待响应操作，自动取消")
            self.handle_response(sid, None, None) 

        # B. 如果当前是逃跑者的回合 -> 强制跳过到下一个人
        current_p = self.players[self.current_player_idx]
        if current_p.sid == sid:
            print("⚠️ 逃跑者正在进行回合，强制结束回合")
            self.pending_action = None # 强清 Pending
            
            # 手动寻找下一个存活者并开始回合 (替代 try_end_turn)
            start_idx = self.current_player_idx
            found_next = False
            for i in range(1, count):
                next_idx = (start_idx + i) % count
                next_p = self.players[next_idx]
                if next_p.is_alive:
                    self.current_player_idx = next_idx
                    self._enter_turn_cycle(next_p)
                    found_next = True
                    break
            
            if not found_next:
                # 双重保险：如果没有下一个人，说明游戏结束
                self.phase = GamePhase.GAME_OVER

        # C. 房主转移
        if p.is_host:
            p.is_host = False
            next_host_idx = (my_idx + 1) % count
            for i in range(count):
                candidate = self.players[(next_host_idx + i) % count]
                if candidate.sid != sid: 
                    candidate.is_host = True
                    print(f"👑 房主权限已转移给 {candidate.nickname}")
                    break

        return msg

    def kill_player(self, victim: Player, killer: Optional[Player]):
        victim.hp = 0
        victim.is_alive = False
        
        if killer:
            print(f"💀 {victim.nickname} 阵亡，遗产归 {killer.nickname}")
            self._transfer_cards(victim, killer)
        else:
            print(f"💀 {victim.nickname} 阵亡，遗产弃置")
            self.deck.discard_pile.extend(victim.hand_cards)
            # 🌟 修复：使用 equips
            for k, card in victim.equips.items():
                if card: self.deck.discard_pile.append(card)
        
        victim.hand_cards = []
        victim.equips = {k: None for k in victim.equips}

        self._check_game_over()

    def _transfer_cards(self, source: Player, target: Player):
        target.hand_cards.extend(source.hand_cards)
        # 🌟 修复：使用 equips
        for k, card in source.equips.items():
            if card:
                target.hand_cards.append(card)

    def _check_game_over(self):
        alive_players = [pl for pl in self.players if pl.is_alive]
        if len(alive_players) <= 1:
            self.phase = GamePhase.GAME_OVER
            if alive_players:
                self.winner_sid = alive_players[0].sid
            else:
                self.winner_sid = None
            
    # --- 核心属性 ---

    def get_distance(self, from_sid: str, to_sid: str) -> int:
        p1, p2 = self.get_player(from_sid), self.get_player(to_sid)
        if not p1 or not p2: return 999
        n = len(self.players)
        if n == 0: return 0
        
        diff = abs(p1.seat_id - p2.seat_id)
        phys_dist = min(diff, n - diff)
        
        plus_mod = 1 if p2.equips["horse_plus"] else 0
        minus_mod = 1 if p1.equips["horse_minus"] else 0
        dist = phys_dist + plus_mod - minus_mod
        
        for skill_name in p1.skills:
            skill = GENERAL_SKILL_REGISTRY.get(skill_name)
            if skill:
                dist = skill.modify_distance(self, p1, p2, dist)
        
        return max(1, dist)

    def can_attack(self, from_sid: str, to_sid: str) -> bool:
        p = self.get_player(from_sid)
        if not p: return False
        weapon = p.equips["weapon"]
        attack_range = weapon.attack_range if weapon else 1
        return attack_range >= self.get_distance(from_sid, to_sid)

    # --- 游戏全生命周期 ---

    def start_game(self) -> Tuple[bool, str]:
        if len(self.players) < 2: return False, "人数不足2人"
        if not all(p.is_ready for p in self.players): return False, "仍有玩家未准备"
        if not self.generals_data: return False, "武将数据未加载"

        self.is_started = True
        self.winner_sid = None
        
        general_ids = [g['id'] for g in self.generals_data]
        random.shuffle(general_ids)
        
        if len(general_ids) < len(self.players) * 3:
            return False, "武将数量不足，无法开局"

        for p in self.players:
            p.general_id = "" 
            p.skills = []
            p.general_candidates = [general_ids.pop() for _ in range(3)]

        self.phase = GamePhase.PICK_GENERAL
        return True, "进入选将阶段"

    def select_general(self, sid: str, general_id: str) -> Tuple[bool, str]:
        if self.phase != GamePhase.PICK_GENERAL: return False, "当前不是选将阶段"
        p = self.get_player(sid)
        if not p: return False, "玩家不存在"
        
        if general_id not in p.general_candidates:
            return False, "该武将不在你的候选列表中"
        
        p.general_id = general_id
        
        all_selected = all(pl.general_id for pl in self.players)
        if all_selected:
            self._finalize_setup()
            return True, "所有玩家选将完毕，游戏开始！"
        
        return True, "选将成功，等待其他玩家..."

    def _finalize_setup(self):
        self.deck.init_deck()
        self.deck.shuffle()
        
        gen_map = {g['id']: g for g in self.generals_data}

        for p in self.players:
            gen_info = gen_map.get(p.general_id)
            if gen_info:
                p.kingdom = gen_info["kingdom"]
                p.max_hp = gen_info["max_hp"]
                p.hp = gen_info["max_hp"]
                p.skills = gen_info["skills"]
            
            p.hand_cards = self.deck.draw(4)
            p.equips = {k: None for k in p.equips}
            p.is_alive = True

        self.current_player_idx = 0
        self._enter_turn_cycle(self.players[0])

    def _enter_turn_cycle(self, player: Player):
        self.phase = GamePhase.DRAW
        
        # 🌟 修复：回合开始重置出杀计数
        player.sha_count = 0
        
        draw_count = 2
        for s_name in player.skills:
            skill = GENERAL_SKILL_REGISTRY.get(s_name)
            if skill:
                draw_count = skill.modify_draw_count(self, player, draw_count)
                
        player.hand_cards.extend(self.deck.draw(draw_count))
        self.phase = GamePhase.PLAY

    def try_end_turn(self, sid: str) -> Tuple[bool, str]:
        if self.pending_action: return False, "有待处理的询问"
        p = self.players[self.current_player_idx]
        if p.sid != sid: return False, "非当前回合"

        limit = max(0, p.hp)
        while len(p.hand_cards) > limit:
            c = p.hand_cards.pop()
            self.deck.discard_pile.append(c)
        
        # 🌟 循环查找下一个存活者
        start_idx = self.current_player_idx
        while True:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            next_p = self.players[self.current_player_idx]
            if next_p.is_alive:
                self._enter_turn_cycle(next_p)
                break
            if self.current_player_idx == start_idx:
                # 转了一圈没人，游戏应该已经结束
                break
                
        return True, "回合已结束"

    # --- 核心战斗 ---

    def apply_damage(self, sid: str, amount: int, source_sid: Optional[str] = None):
        p = self.get_player(sid)
        if p and p.is_alive:
            p.hp -= amount
            if p.hp <= 0:
                killer = self.get_player(source_sid) if source_sid else None
                self.kill_player(p, killer)

    def play_card(self, sid: str, index: int, target_sid: Optional[str]) -> Tuple[bool, str, Optional[Card]]:
        if self.pending_action or self.phase == GamePhase.GAME_OVER: 
            return False, "当前禁止此项操作", None
        
        p = self.get_player(sid)
        if not p or not p.is_alive or self.players[self.current_player_idx].sid != sid: 
            return False, "不是你的回合或已死亡", None
        if index >= len(p.hand_cards): return False, "手牌索引无效", None
        
        card = p.hand_cards[index]

        # 🌟 意图推断修复
        real_skill_name = card.name
        can_transform = False
        
        # 1. 意图：出杀 (非杀牌 -> 杀)
        if target_sid and card.name != "杀" and card.name != "决斗" and card.name != "南蛮入侵" and card.name != "万箭齐发":
             for s_name in p.skills:
                 skill = GENERAL_SKILL_REGISTRY.get(s_name)
                 if skill and skill.can_transform_card(p, card, "杀"):
                     real_skill_name = "杀"
                     can_transform = True
                     print(f"⚔️ {p.nickname} 触发【{skill.name}】：{card.name} -> 杀")
                     break
        
        # 2. 询问：技能确认
        if card.name == "杀" and target_sid:
            for s_name in p.skills:
                skill = GENERAL_SKILL_REGISTRY.get(s_name)
                if skill and s_name == "qixi" and skill.can_transform_card(p, card, "过河拆桥"):
                    self.pending_action = PendingAction(
                        source_sid=sid, target_sid=sid, card_id=card.card_id,
                        action_type=PendingType.ASK_FOR_SKILL_CONFIRM,
                        extra_data={
                            "skill_name": "奇袭", "origin_name": "杀", "transform_name": "过河拆桥",
                            "card_index": index, "target_sid": target_sid
                        }
                    )
                    return True, "请确认卡牌用途", None
        
        if target_sid and (card.name == "杀" or card.card_type.name.startswith("EQUIP")):
             for s_name in p.skills:
                skill = GENERAL_SKILL_REGISTRY.get(s_name)
                if skill and s_name == "guose" and skill.can_transform_card(p, card, "乐不思蜀"):
                    self.pending_action = PendingAction(
                        source_sid=sid, target_sid=sid, card_id=card.card_id,
                        action_type=PendingType.ASK_FOR_SKILL_CONFIRM,
                        extra_data={
                            "skill_name": "国色", "origin_name": card.name, "transform_name": "乐不思蜀",
                            "card_index": index, "target_sid": target_sid
                        }
                    )
                    return True, "请确认卡牌用途", None

        # 3. 意图：默认转化
        if target_sid and card.name != "过河拆桥" and card.name != "杀" and not can_transform:
             for s_name in p.skills:
                 skill = GENERAL_SKILL_REGISTRY.get(s_name)
                 if skill and skill.can_transform_card(p, card, "过河拆桥"):
                     real_skill_name = "过河拆桥"
                     can_transform = True
                     break
                     
        if target_sid and card.name != "乐不思蜀" and card.name != "杀" and not can_transform:
             for s_name in p.skills:
                 skill = GENERAL_SKILL_REGISTRY.get(s_name)
                 if skill and skill.can_transform_card(p, card, "乐不思蜀"):
                     real_skill_name = "乐不思蜀"
                     can_transform = True
                     break

        skill_strategy = None
        if card.card_type.name.startswith("EQUIP"):
            skill_strategy = SKILL_REGISTRY.get("equip_handler")
        else:
            skill_strategy = SKILL_REGISTRY.get(real_skill_name)

        if not skill_strategy: return False, f"卡牌/技能 【{real_skill_name}】 逻辑未定义", None

        is_valid, err_msg = skill_strategy.validate(self, p, card, target_sid)
        if not is_valid: return False, err_msg, None

        success, msg = skill_strategy.execute(self, p, card, target_sid)
        
        if success:
            if can_transform: msg = f"(转化) {msg}"
            return True, msg, card
        else:
            return False, msg, None

    def handle_response(self, sid: str, card_index: Optional[int], target_area: Optional[str] = None) -> Tuple[bool, str]:
        if not self.pending_action or self.pending_action.target_sid != sid: return False, "无须响应"
        act = self.pending_action
        p_self = self.get_player(sid)

        # 技能确认
        if act.action_type == PendingType.ASK_FOR_SKILL_CONFIRM:
            use_skill = (target_area == "use_skill")
            ctx = act.extra_data
            original_idx = ctx["card_index"]
            original_target = ctx["target_sid"]
            transform_name = ctx["transform_name"]
            
            self.pending_action = None
            
            card = p_self.hand_cards[original_idx]
            final_name = transform_name if use_skill else card.name
            
            skill_strategy = SKILL_REGISTRY.get(final_name)
            if not skill_strategy: return False, "技能执行失败"
            
            success, msg = skill_strategy.execute(self, p_self, card, original_target)
            if success:
                return True, f"使用了 {final_name}" + (" (转化)" if use_skill else "")
            else:
                return False, msg

        if act.action_type == PendingType.ASK_FOR_SHAN:
            if card_index is not None:
                if card_index >= len(p_self.hand_cards): return False, "卡牌索引无效"
                c = p_self.hand_cards[card_index]
                
                is_valid_shan = (c.name == "闪")
                if not is_valid_shan:
                    for s_name in p_self.skills:
                        skill = GENERAL_SKILL_REGISTRY.get(s_name)
                        if skill and skill.can_transform_card(p_self, c, "闪"):
                            is_valid_shan = True
                            print(f"🛡️ {p_self.nickname} 触发【{skill.name}】：{c.name} -> 闪")
                            break
                
                if is_valid_shan:
                    p_self.hand_cards.pop(card_index); self.deck.discard_pile.append(c)
                    self.pending_action = None
                    return True, "已出【闪】(或转化)，成功抵消攻击"
            
            self.apply_damage(sid, 1, source_sid=act.source_sid)
            self.pending_action = None
            return True, "未响应【闪】，受到了1点伤害"

        if act.action_type == PendingType.ASK_FOR_DISMANTLE:
            target_p = self.get_player(act.extra_data["target_to_dismantle"])
            if not target_p: return False, "目标已离线"
            self._move_card(target_p, p_self, target_area, to_hand=False)
            self.pending_action = None
            return True, "已成功拆除对方的牌"

        if act.action_type == PendingType.ASK_FOR_SNATCH:
            target_p = self.get_player(act.extra_data["target_to_snatch"])
            if not target_p: return False, "目标已离线"
            self._move_card(target_p, p_self, target_area, to_hand=True)
            self.pending_action = None
            return True, "顺手牵羊成功"

        return False, "无效操作"

    def _move_card(self, from_p: Player, to_p: Player, area: str, to_hand: bool):
        card = None
        if area == "hand" and from_p.hand_cards:
            import random
            idx = random.randint(0, len(from_p.hand_cards)-1)
            card = from_p.hand_cards.pop(idx) 
        elif area in from_p.equips:
            card = from_p.equips[area]
            if card: from_p.equips[area] = None
        
        if card:
            if to_hand: to_p.hand_cards.append(card)
            else: self.deck.discard_pile.append(card)

    def get_public_state(self):
        return {
            "room_id": self.room_id, "phase": self.phase, "current_seat": self.players[self.current_player_idx].seat_id if self.players else 0,
            "is_started": self.is_started, "deck_count": len(self.deck.draw_pile),
            "pending": self.pending_action.model_dump() if self.pending_action else None,
            "winner_sid": self.winner_sid,
            "players": [
                {
                    "sid": p.sid, "seat_id": p.seat_id, "hp": p.hp, "max_hp": p.max_hp,
                    "username": p.username, "nickname": p.nickname, "avatar": p.avatar,
                    "general_id": p.general_id,
                    "candidates": p.general_candidates if self.phase == GamePhase.PICK_GENERAL else [],
                    "kingdom": p.kingdom,
                    "is_alive": p.is_alive, "is_ready": p.is_ready, "is_host": p.is_host,
                    "card_count": len(p.hand_cards),
                    "equips": {k: (v.name if v else None) for k, v in p.equips.items()}
                } for p in self.players
            ]
        }