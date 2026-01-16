<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { socket } from './services/socket';
import { useUserStore } from './stores/userStore'; 
import GameCard from './components/GameCard.vue';
import PlayerAvatar from './components/PlayerAvatar.vue';
import Login from './components/Login.vue'; 
import GeneralSelector from './components/GeneralSelector.vue';
import RoomList from './components/RoomList.vue'; 

// === 0. 用户系统集成 ===
const userStore = useUserStore();

watch(() => userStore.isLoggedIn, (newVal) => {
  if (newVal && userStore.token) {
    socket.auth = { token: userStore.token }; 
    socket.connect();
  } else {
    socket.disconnect(); 
  }
});

// === 1. 数据基础状态 ===
const inRoom = ref(false);        
const handCards = ref([]);        
const playedCards = ref([]);        
const players = ref([]);            
const gameState = ref({ 
  phase: 'waiting', 
  current_seat: 0, 
  room_id: '', 
  is_started: false, 
  deck_count: 0,
  pending: null,      
  winner_sid: null  
});
const systemMsg = ref("");        

// === 2. 交互状态控制 ===
// 单选 (普通出牌)
const selectedHandIndex = ref(-1);
const selectedTargetSid = ref(null);

// 多选 (弃牌/技能模式)
const selectedSkillCards = ref([]);   // Array<int>
const selectedSkillTargets = ref([]); // Array<str>
const skillMode = ref(null);          // 当前激活的主动技能名 (如 'qixi')

// 弹窗状态
const showProfileModal = ref(false);
const currentProfile = ref(null);
const viewingSkill = ref(null); // 当前正在阅读详情的技能ID

// === 3. 计算属性逻辑 ===
const mySid = computed(() => socket.id);
const me = computed(() => players.value.find(p => p.sid === mySid.value));
const isHost = computed(() => me.value?.is_host || false);

// === 技能字典 (完整版) ===
const skillMap = {
  "jianxiong": "奸雄", "hujia": "护驾", "tiandu": "天妒", "yiji": "遗计",
  "fankui": "反馈", "guicai": "鬼才", "ganglie": "刚烈", "tuxi": "突袭",
  "luoyi": "裸衣", "luoshen": "洛神", "qingguo": "倾国", "rende": "仁德",
  "jijiang": "激将", "wusheng": "武圣", "paoxiao": "咆哮", "guanxing": "观星",
  "kongcheng": "空城", "longdan": "龙胆", "mashu": "马术", "tieqi": "铁骑",
  "jizhi": "集智", "qicai": "奇才", "zhiheng": "制衡", "jiuyuan": "救援",
  "qixi": "奇袭", "keji": "克己", "kurou": "苦肉", "yingzi": "英姿",
  "fanjian": "反间", "guose": "国色", "liuli": "流离", "qianxun": "谦逊",
  "lianying": "连营", "jieyin": "结姻", "xiaoji": "枭姬", "qingnang": "青囊",
  "jijiu": "急救", "wushuang": "无双", "lijian": "离间", "biyue": "闭月",
  "yongsi": "庸肆", "weidi": "伪帝", "yaowu": "耀武", "fuyong": "负勇"
};

const skillDescriptions = {
  // 魏
  "jianxiong": "【奸雄】锁定技，当你受到伤害后，你可以获得对你造成伤害的牌。",
  "hujia": "【护驾】主公技，当你需要使用或打出【闪】时，你可以令其他魏势力角色打出一张【闪】。",
  "tiandu": "【天妒】锁定技，当你的判定牌生效后，你获得此牌。",
  "yiji": "【遗计】当你受到1点伤害后，你可以观看牌堆顶的两张牌，将这些牌交给任意角色。",
  "fankui": "【反馈】当你受到伤害后，你可以获得伤害来源的一张牌。",
  "guicai": "【鬼才】当一名角色的判定牌生效前，你可以打出一张手牌代替之。",
  "ganglie": "【刚烈】当你受到伤害后，你可以进行判定：若不为红桃，伤害来源选择一项：1.弃置两张手牌；2.受到1点伤害。",
  "tuxi": "【突袭】摸牌阶段，你可以放弃摸牌，改为获得一至两名其他角色的各一张手牌。",
  "luoyi": "【裸衣】摸牌阶段，你可以少摸一张牌，本回合你使用【杀】或【决斗】造成的伤害+1。",
  "luoshen": "【洛神】准备阶段，你可以进行判定，若为黑色，你获得此牌，并可继续判定。",
  "qingguo": "【倾国】你可以将一张黑色手牌当【闪】使用或打出。",
  
  // 蜀
  "rende": "【仁德】出牌阶段，你可以将任意张手牌交给其他角色。给牌达两张或更多时，你摸一张牌。",
  "jijiang": "【激将】主公技，当你需要使用或打出【杀】时，你可以令其他蜀势力角色打出一张【杀】。",
  "wusheng": "【武圣】你可以将一张红色牌当【杀】使用或打出。",
  "paoxiao": "【咆哮】锁定技，你使用【杀】无次数限制。",
  "guanxing": "【观星】准备阶段，你可以观看牌堆顶的X张牌（X为存活人数且最多为5），调整顺序。",
  "kongcheng": "【空城】锁定技，当你没有手牌时，你不能成为【杀】或【决斗】的目标。",
  "longdan": "【龙胆】你可以将【杀】当【闪】，【闪】当【杀】使用或打出。",
  "mashu": "【马术】锁定技，你计算与其他角色的距离-1。",
  "tieqi": "【铁骑】当你使用【杀】指定目标后，你可以进行判定，若为红色，此【杀】不可被闪避。",
  "jizhi": "【集智】当你使用锦囊牌时，你可以摸一张牌。",
  "qicai": "【奇才】锁定技，你使用锦囊牌无距离限制。",
  
  // 吴
  "zhiheng": "【制衡】出牌阶段限一次，你可以弃置任意张牌，然后摸等量的牌。",
  "jiuyuan": "【救援】主公技，其他吴势力角色对你使用【桃】回复的体力+1。",
  "qixi": "【奇袭】你可以将一张黑色牌当【过河拆桥】使用。",
  "keji": "【克己】若你于出牌阶段未出【杀】，跳过弃牌阶段。",
  "kurou": "【苦肉】出牌阶段，你可以失去1点体力，然后摸两张牌。",
  "yingzi": "【英姿】摸牌阶段，你可以多摸一张牌。",
  "fanjian": "【反间】出牌阶段限一次，令一名角色猜花色，猜错则受1点伤害。",
  "guose": "【国色】你可以将一张方块牌当【乐不思蜀】使用。",
  "liuli": "【流离】成为【杀】的目标时，你可以弃置一张牌，将此【杀】转移给攻击范围内的其他角色。",
  "qianxun": "【谦逊】锁定技，你不能成为【顺手牵羊】和【乐不思蜀】的目标。",
  "lianying": "【连营】当你失去最后一张手牌时，你可以摸一张牌。",
  "jieyin": "【结姻】出牌阶段限一次，你可以弃置两张手牌，令你和一名男性角色各回复1点体力。",
  "xiaoji": "【枭姬】当你失去装备区的一张牌时，你可以摸两张牌。",
  
  // 群
  "qingnang": "【青囊】出牌阶段限一次，你可以弃置一张手牌，令一名角色回复1点体力。",
  "jijiu": "【急救】你的回合外，你可以将一张红色牌当【桃】使用。",
  "wushuang": "【无双】锁定技，你使用【杀】需两张【闪】抵消；决斗每次需打出两张【杀】。",
  "lijian": "【离间】出牌阶段限一次，你可以弃置一张牌，令两名男性角色拼杀。",
  "biyue": "【闭月】结束阶段，你可以摸一张牌。",
  "yongsi": "【庸肆】锁定技，摸牌阶段多摸一张；弃牌阶段需维持手牌数等于体力值。",
  "weidi": "【伪帝】主公技，你拥有当前主公的主公技。",
  "yaowu": "【耀武】锁定技，受到红杀伤害时，伤害来源摸一张牌。",
  "fuyong": "【负勇】锁定技，濒死时不能求桃。"
};

const getSkillName = (code) => skillMap[code] || code;
const getSkillDesc = (code) => skillDescriptions[code] || "暂无详细说明。";

// === 核心状态判定 ===

// 是否轮到我出牌
const isMyTurn = computed(() => {
  if (!players.value.length || gameState.value.pending || gameState.value.phase === 'game_over') return false; 
  const currentP = players.value.find(p => p.seat_id === gameState.value.current_seat);
  return gameState.value.is_started && 
         currentP && 
         currentP.sid === mySid.value && 
         gameState.value.phase === 'play';
});

// 是否需要我响应
const isMyResponse = computed(() => {
  return gameState.value.pending && gameState.value.pending.target_sid === mySid.value;
});

// 是否处于弃牌阶段 (重要：触发多选逻辑)
const isDiscarding = computed(() => {
  return isMyResponse.value && gameState.value.pending.action_type === 'ask_for_discard';
});

// 是否需要显示全屏遮罩 (模态窗口)
// 注意：isDiscarding 也算模态，因为需要显示“请弃置X张牌”的提示框
const isModalResponse = computed(() => {
  if (isDiscarding.value) return true;
  if (!isMyResponse.value) return false;
  const type = gameState.value.pending.action_type;
  return [
    'ask_for_shan', 'ask_for_sha', 'ask_for_skill_confirm', 
    'ask_for_choose_card', 'ask_for_yiji', 'ask_for_ganglie', 'ask_for_collateral'
  ].includes(type);
});

// 筛选当前可用的主动技能 (Active Skills)
// 这些技能需要显示按钮，点击后手动选择牌/目标
const activeSkills = computed(() => {
  if (!me.value) return [];
  const actives = [
    'lijian', 'qingnang', 'rende', 'kurou', 'jieyin', 
    'fanjian', 'zhiheng', 'qixi', 'guose' // 🌟 重点：奇袭、国色现在是主动技
  ];
  return me.value.skills.filter(s => actives.includes(s));
});

// 辅助判定
const hasShan = computed(() => handCards.value.some(c => c.name === '闪'));
const hasSha = computed(() => handCards.value.some(c => c.name === '杀'));
const showGeneralSelector = computed(() => gameState.value.phase === 'pick_general' && me.value && !me.value.general_id);
const isWaitingOthers = computed(() => gameState.value.phase === 'pick_general' && me.value && me.value.general_id);

// === 4. 生命周期 ===
onMounted(() => {
  if (userStore.isLoggedIn && userStore.token) {
    socket.auth = { token: userStore.token };
    socket.connect();
  }
  socket.on('connect_error', () => { showToast("⚠️ 连接失败，请重新登录"); userStore.logout(); });
  socket.on('hand_update', (data) => { handCards.value = data.cards; });
  socket.on('room_update', (data) => { players.value = data.players; gameState.value = data; inRoom.value = true; });
  socket.on('kicked', () => { resetToLobby(); showToast("🚫 你已被房主踢出房间"); });
  socket.on('game_started', () => { playedCards.value = []; showToast("⚔️ 战火燃起！"); });
  socket.on('player_played', (data) => {
    playedCards.value.push(data.card);
    if (playedCards.value.length > 5) playedCards.value.shift();
    if (data.player_id === socket.id) resetSelection();
  });
  socket.on('system_message', (data) => showToast(data.msg));
});

onUnmounted(() => { socket.off(); socket.disconnect(); });

// === 5. 交互方法 ===

const joinRoom = (roomId) => { socket.emit('join_room', { room_id: roomId }); };
const toggleReady = () => socket.emit('toggle_ready', {});
const startGame = () => socket.emit('start_game', {});
const onSelectGeneral = (genId) => { socket.emit('select_general', { general_id: genId }); };
const endTurn = () => {
  if (gameState.value.pending) return showToast("请先完成当前操作");
  socket.emit('end_turn', {});
};
const resetToLobby = () => {
  socket.emit('leave_room', {}); inRoom.value = false; socket.emit('get_lobby', {});
  handCards.value = []; playedCards.value = []; players.value = [];
  gameState.value = { phase: 'waiting', current_seat: 0, room_id: '', is_started: false, deck_count: 0, pending: null, winner_sid: null };
  resetSelection();
};

// 🌟 卡牌选择逻辑 (核心修复)
const selectCard = (index) => {
  // 弃牌模式 OR 技能模式 -> 启用多选
  if (isDiscarding.value || skillMode.value) {
    const i = selectedSkillCards.value.indexOf(index);
    if (i > -1) selectedSkillCards.value.splice(i, 1); // 取消
    else selectedSkillCards.value.push(index); // 选中
    return;
  }
  // 普通模式 -> 单选
  selectedHandIndex.value = (selectedHandIndex.value === index) ? -1 : index;
};

// 目标选择
const selectTarget = (sid) => {
  if (sid === mySid.value) return; 
  
  if (skillMode.value) { // 技能多选目标 (如离间)
    const i = selectedSkillTargets.value.indexOf(sid);
    if (i > -1) selectedSkillTargets.value.splice(i, 1);
    else selectedSkillTargets.value.push(sid);
    return;
  }
  
  if (gameState.value.pending?.action_type === 'ask_for_yiji') {
     selectedTargetSid.value = sid; return;
  }
  
  selectedTargetSid.value = (selectedTargetSid.value === sid) ? null : sid;
};

const handleAvatarClick = (player) => {
  // 只有在游戏开始后才允许选人
  if (gameState.value.is_started) selectTarget(player.sid);
  else openProfile(player);
};

// 技能详情查看 (点击切换)
const toggleSkillInfo = (skillId) => {
  if (viewingSkill.value === skillId) viewingSkill.value = null;
  else viewingSkill.value = skillId;
};
const closeSkillInfo = () => { viewingSkill.value = null; };

// 确认出牌
const confirmPlay = () => {
  if (selectedHandIndex.value === -1) return;
  const card = handCards.value[selectedHandIndex.value];
  const needsTarget = ['杀', '顺手牵羊', '过河拆桥', '决斗', '借刀杀人'].includes(card.name);
  if (needsTarget && !selectedTargetSid.value) return showToast("⚠️ 请选择目标");
  socket.emit('play_card', { card_index: selectedHandIndex.value, target_sid: selectedTargetSid.value });
};

// 响应操作
const respondAction = (useCardIndex = null, area = null, extra = null) => {
  socket.emit('respond_action', { card_index: useCardIndex, target_area: area, extra_payload: extra });
  resetSelection();
};

// 确认弃牌
const confirmDiscard = () => {
  const req = gameState.value.pending.extra_data.discard_count;
  if (selectedSkillCards.value.length !== req) return showToast(`请选择 ${req} 张牌`);
  respondAction(null, null, { indices: selectedSkillCards.value });
  selectedSkillCards.value = [];
};

// 确认遗计
const confirmYiji = () => {
  if (selectedHandIndex.value === -1 || !selectedTargetSid.value) return showToast("请选一张牌和一个目标");
  const card = handCards.value[selectedHandIndex.value];
  respondAction(null, null, { target_id: selectedTargetSid.value, card_id: card.card_id });
};

// 切换技能模式
const toggleSkillMode = (skill) => {
  if (skillMode.value === skill) {
    skillMode.value = null; selectedSkillTargets.value = []; selectedSkillCards.value = [];
  } else {
    skillMode.value = skill; selectedSkillTargets.value = []; selectedSkillCards.value = [];
    showToast(`已进入【${getSkillName(skill)}】模式，请选择操作对象`);
  }
};

// 发动技能
const fireSkill = () => {
  if (!skillMode.value) return;
  socket.emit('use_skill', {
    skill_name: skillMode.value,
    targets: selectedSkillTargets.value,
    card_indices: selectedSkillCards.value
  });
  toggleSkillMode(null);
};

const resetSelection = () => {
  selectedHandIndex.value = -1; selectedTargetSid.value = null;
  selectedSkillCards.value = []; selectedSkillTargets.value = []; skillMode.value = null;
};

const showToast = (msg) => { systemMsg.value = msg; setTimeout(() => { systemMsg.value = ""; }, 3000); };
const openProfile = (player) => { currentProfile.value = player; showProfileModal.value = true; };
const closeProfile = () => { showProfileModal.value = false; currentProfile.value = null; };
const kickCurrentPlayer = () => { if (currentProfile.value) { socket.emit('kick_player', { target_sid: currentProfile.value.sid }); closeProfile(); } };
</script>

<template>
  <div class="sgs-app-root">
    
    <transition name="fade">
      <div v-if="systemMsg" class="app-toast"><div class="toast-content">📜 {{ systemMsg }}</div></div>
    </transition>

    <transition name="zoom">
      <GeneralSelector v-if="showGeneralSelector" :candidates="me?.candidates || []" @select="onSelectGeneral" />
    </transition>

    <transition name="fade">
      <div v-if="isWaitingOthers" class="waiting-overlay-full">
        <div class="waiting-text"><div class="spinner"></div>正在等待其他诸侯点将...</div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showProfileModal && currentProfile" class="profile-overlay" @click.self="closeProfile">
        <div class="profile-card">
          <div class="profile-header">
            <span class="p-kingdom" :class="currentProfile.kingdom">{{ currentProfile.kingdom?.toUpperCase() }}</span>
            <span class="p-name">{{ currentProfile.nickname }}</span>
          </div>
          <div class="p-content">
            <img :src="`/avatars/${currentProfile.avatar}`" class="p-avatar-large">
            <div class="p-info">
              <p>账号: {{ currentProfile.username }}</p>
              <p>武将: {{ currentProfile.general_id ? '已选' : '未选' }}</p>
              <p>手牌数: {{ currentProfile.card_count }}</p>
            </div>
          </div>
          <div class="p-actions">
            <button v-if="isHost && currentProfile.sid !== mySid && !gameState.is_started" class="btn-kick" @click="kickCurrentPlayer">👢 踢出房间</button>
            <button class="btn-close" @click="closeProfile">关闭</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="zoom">
      <div v-if="gameState.phase === 'game_over'" class="victory-overlay">
        <div class="victory-modal">
          <h1 class="v-title" :class="{ win: gameState.winner_sid === mySid }">{{ gameState.winner_sid === mySid ? '🏆 凯旋归来' : '💀 战死沙场' }}</h1>
          <p class="v-info">获胜者: {{ players.find(p => p.sid === gameState.winner_sid)?.seat_id }}号位</p>
          <button class="btn-restart" @click="resetToLobby">回到大厅</button>
        </div>
      </div>
    </transition>

    <transition name="pop">
      <div v-if="isModalResponse" class="global-response-overlay">
         
         <div v-if="gameState.pending?.action_type === 'ask_for_choose_card'" class="wugu-container">
            <div class="wugu-title">🌾 五 谷 丰 登 🌾</div>
            <div class="wugu-tips">请选择一张卡牌获得</div>
            <div class="wugu-cards">
               <GameCard v-for="(c, idx) in gameState.pending.extra_data.wugu_cards" :key="idx" :card="c" class="wugu-card-item" @click="respondAction(idx)" />
            </div>
         </div>

         <div v-else class="response-decree">
             <div class="decree-header"><span class="decree-icon">📜</span> 军令状</div>
             
             <div v-if="gameState.pending?.action_type === 'ask_for_discard'" class="decree-content">
                <h3>📦 弃牌阶段</h3>
                <p>请弃置 {{ gameState.pending.extra_data.discard_count }} 张牌</p>
                <p class="sub-text">已选中: {{ selectedSkillCards.length }} 张</p>
                <div class="decree-btns">
                  <button class="btn-decree confirm" @click="confirmDiscard">确认弃牌</button>
                </div>
             </div>

             <div v-else-if="gameState.pending?.action_type === 'ask_for_skill_confirm'" class="decree-content">
                <h3>⚔️ 技能发动确认</h3>
                <p>是否发动【{{ gameState.pending.extra_data.skill_name }}】<br>将牌转化为【{{ gameState.pending.extra_data.transform_name }}】？</p>
                <div class="decree-btns">
                  <button class="btn-decree confirm" @click="respondAction(null, 'use_skill')">确认发动</button>
                  <button class="btn-decree cancel" @click="respondAction(null, 'cancel')">取消</button>
                </div>
             </div>

             <div v-else-if="gameState.pending?.action_type === 'ask_for_shan'" class="decree-content">
                <h3>🛡️ 敌军杀来！</h3>
                <p>请打出一张【闪】</p>
                <div class="decree-btns">
                  <button class="btn-decree confirm" @click="respondAction(handCards.findIndex(c => c.name === '闪'))">出闪 {{ hasShan ? '' : '(转化)' }}</button>
                  <button class="btn-decree cancel" @click="respondAction(null)">放弃 (掉血)</button>
                </div>
             </div>

             <div v-else-if="gameState.pending?.action_type === 'ask_for_sha'" class="decree-content">
                <h3>⚔️ 决一死战！</h3>
                <p>请打出一张【杀】</p>
                <div class="decree-btns">
                  <button class="btn-decree confirm" @click="respondAction(handCards.findIndex(c => c.name === '杀'))">出杀 {{ hasSha ? '' : '(转化)' }}</button>
                  <button class="btn-decree cancel" @click="respondAction(null)">放弃 (掉血)</button>
                </div>
             </div>

             <div v-else-if="gameState.pending?.action_type === 'ask_for_collateral'" class="decree-content">
                <h3>🔪 借刀杀人</h3>
                <p>请交出武器</p>
                <div class="decree-btns">
                  <button class="btn-decree confirm" @click="respondAction(null)">交出武器</button>
                </div>
             </div>
             
             <div v-else-if="gameState.pending?.action_type === 'ask_for_ganglie'" class="decree-content">
                <h3>😡 刚烈判定</h3>
                <p>是否发动刚烈？</p>
                <div class="decree-btns">
                  <button class="btn-decree confirm" @click="respondAction(null, 'confirm')">发动</button>
                  <button class="btn-decree cancel" @click="respondAction(null, 'cancel')">放弃</button>
                </div>
             </div>

             <div v-else-if="gameState.pending?.action_type === 'ask_for_yiji'" class="decree-content">
                <h3>💙 遗计分牌</h3>
                <p>请在下方选择一张手牌，并点击一名目标头像</p>
                <div class="decree-btns">
                  <button class="btn-decree confirm" @click="confirmYiji">确认分配</button>
                  <button class="btn-decree cancel" @click="respondAction(null)">结束分配</button>
                </div>
             </div>
         </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="viewingSkill" class="skill-detail-modal-overlay" @click.self="closeSkillInfo">
        <div class="skill-detail-card">
          <div class="sd-header">
            <span>{{ getSkillName(viewingSkill) }}</span>
            <button class="sd-close" @click="closeSkillInfo">×</button>
          </div>
          <div class="sd-body">
            {{ getSkillDesc(viewingSkill) }}
          </div>
        </div>
      </div>
    </transition>

    <Login v-if="!userStore.isLoggedIn" />

    <div v-else-if="!inRoom" class="lobby-view">
      <div class="user-profile-bar">
        <div class="profile-left">
          <div class="avatar-frame"><img :src="`/avatars/${userStore.user?.avatar || 'default.png'}`" class="user-avatar-small" /></div>
          <div class="user-details">
            <div class="user-nickname">{{ userStore.user?.nickname || '未知武将' }}</div>
            <div class="user-account">@{{ userStore.user?.username }}</div>
          </div>
        </div>
        <button class="btn-logout-seal" @click="userStore.logout()" title="注销/撤退"><span>注</span><span>销</span></button>
      </div>
      <RoomList @join="joinRoom" />
    </div>

    <div v-else class="game-container">
      <div class="top-bar">
        <div class="room-info">
          <span class="label">战场:</span> {{ gameState.room_id }}号营 <span class="divider">|</span>
          <span class="label">剩余牌堆:</span> {{ gameState.deck_count }}
        </div>
        <div class="top-actions"><button class="btn-wood-small" @click="resetToLobby">撤退</button></div>
      </div>

      <div class="battlefield">
        <div class="opponents-row">
          <div v-for="p in players.filter(p => p.sid !== mySid)" :key="p.sid" class="player-slot">
            <PlayerAvatar 
              :player="p" 
              :is-current="gameState.current_seat === p.seat_id"
              :is-selected="selectedTargetSid === p.sid || selectedSkillTargets.includes(p.sid)"
              @click="handleAvatarClick(p)" 
            />
            <div v-if="!gameState.is_started" class="ready-tag" :class="{ ok: p.is_ready }">{{ p.is_ready ? '已准备' : '未准备' }}</div>
            
            <transition name="fade">
              <div v-if="gameState.pending?.source_sid === mySid && (gameState.pending?.action_type === 'ask_for_snatch' || gameState.pending?.action_type === 'ask_for_dismantle') && (gameState.pending?.extra_data.target_to_snatch === p.sid || gameState.pending?.extra_data.target_to_dismantle === p.sid)" class="floating-menu">
                 <div class="menu-header">{{ gameState.pending?.action_type === 'ask_for_snatch' ? '🖐️ 顺手牵羊' : '🔥 过河拆桥' }}</div>
                 <div class="menu-items">
                   <button class="menu-item" @click="respondAction(null, 'hand')">🖐️ 手牌 (随机)</button>
                   <button v-if="p.equips.weapon" class="menu-item" @click="respondAction(null, 'weapon')">⚔️ 武器: {{p.equips.weapon}}</button>
                   <button v-if="p.equips.armor" class="menu-item" @click="respondAction(null, 'armor')">🛡️ 防具: {{p.equips.armor}}</button>
                   <button v-if="p.equips.horse_plus" class="menu-item" @click="respondAction(null, 'horse_plus')">🐎 +1马</button>
                   <button v-if="p.equips.horse_minus" class="menu-item" @click="respondAction(null, 'horse_minus')">🐎 -1马</button>
                 </div>
              </div>
            </transition>
          </div>
        </div>

        <div class="desk-area">
          <transition-group name="card-pop" tag="div" class="played-pile">
            <GameCard v-for="c in playedCards" :key="c.card_id" :card="c" class="desk-card" />
          </transition-group>
        </div>
      </div>

      <div class="control-panel">
        <div class="my-info-group">
          <div class="my-avatar-area"><PlayerAvatar :player="me" :is-me="true" :is-current="isMyTurn" /></div>
          
          <div v-if="me?.general_id" class="my-skills-box">
            <div class="skills-label">技能</div>
            <div class="skills-list">
              <div v-for="skill in me.skills" :key="skill" class="skill-tag" @click="toggleSkillInfo(skill)">
                {{ getSkillName(skill) }}
              </div>
            </div>
          </div>
        </div>

        <div class="my-hand-zone" :class="{ 'highlight-zone': isDiscarding || skillMode }">
          <div class="hand-scroll-wrapper">
            <transition-group name="hand" tag="div" class="hand-cards-row">
              <GameCard 
                v-for="(card, index) in handCards" :key="card.card_id" :card="card"
                class="hand-card-item"
                :class="{ selected: selectedHandIndex === index || selectedSkillCards.includes(index) }" 
                @click="selectCard(index)"
              />
            </transition-group>
          </div>
        </div>

        <div class="command-zone">
          <div v-if="!gameState.is_started" class="pre-game-btns">
             <button v-if="isHost" class="btn-gold-large" @click="startGame">点兵出征</button>
             <button v-else class="btn-wood-large" :class="{ ready: me?.is_ready }" @click="toggleReady">{{ me?.is_ready ? '已备战' : '整备' }}</button>
          </div>

          <div v-else class="combat-controls">
            <div class="turn-indicator" v-if="!isMyTurn">
              <span class="wait-icon">⏳</span> <span>等待 {{ gameState.current_seat }}号位</span>
            </div>
            
            <div v-else-if="skillMode" class="my-turn-actions skill-mode">
              <div class="turn-title" style="color: #2980b9">✨ 发动：{{ getSkillName(skillMode) }}</div>
              <div class="sub-text">已选牌: {{ selectedSkillCards.length }} | 已选人: {{ selectedSkillTargets.length }}</div>
              <div class="btn-group-vertical">
                 <button class="btn-action confirm" @click="fireSkill">确定发动</button>
                 <button class="btn-action cancel" @click="toggleSkillMode(null)">取消</button>
              </div>
            </div>
            
            <div v-else class="my-turn-actions">
              <div class="turn-title">🔥 你的回合</div>
              <div class="btn-group-vertical">
                <button class="btn-action confirm" :disabled="selectedHandIndex === -1" @click="confirmPlay">出牌</button>
                <button class="btn-action cancel" @click="endTurn">结束回合</button>
              </div>
              <div v-if="activeSkills.length" class="active-skills-row">
                 <button v-for="s in activeSkills" :key="s" class="btn-skill" @click="toggleSkillMode(s)">{{ getSkillName(s) }}</button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* 基础容器 */
.sgs-app-root { width: 100%; height: 100%; color: #fff; display: flex; flex-direction: column; }

/* Toast */
.app-toast { position: fixed; top: 15%; left: 50%; transform: translateX(-50%); z-index: 9999; pointer-events: none; }
.toast-content { background: rgba(0, 0, 0, 0.9); color: #f1c40f; padding: 15px 40px; border-radius: 4px; border: 2px solid #8d6e63; font-size: 20px; font-family: 'LiSu', serif; box-shadow: 0 10px 30px rgba(0,0,0,0.8); text-shadow: 0 2px 4px #000; }

/* 遮罩 */
.waiting-overlay-full { position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 999; display: flex; justify-content: center; align-items: center; }
.waiting-text { font-size: 24px; color: #d4af37; display: flex; flex-direction: column; align-items: center; gap: 20px; font-family: 'LiSu', serif; }
.spinner { width: 50px; height: 50px; border: 4px solid rgba(212,175,55,0.2); border-top-color: #d4af37; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 胜利结算 */
.victory-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 9999; display: flex; justify-content: center; align-items: center; }
.victory-modal { background: #111; padding: 50px 80px; border: 4px solid #f1c40f; border-radius: 12px; text-align: center; box-shadow: 0 0 50px rgba(241, 196, 15, 0.3); }
.v-title { font-size: 5em; margin: 0 0 20px 0; color: #7f8c8d; font-family: 'LiSu', serif; }
.v-title.win { color: #f1c40f; text-shadow: 0 0 20px #f1c40f, 0 0 40px #e67e22; background: linear-gradient(to bottom, #fff, #f1c40f, #e67e22); -webkit-background-clip: text; color: transparent; }
.v-info { color: #aaa; font-size: 1.5em; margin-bottom: 30px; }
.btn-restart { padding: 12px 40px; background: #f1c40f; border: none; font-weight: bold; cursor: pointer; border-radius: 4px; color: #3e2723; font-size: 1.2em; }

/* 五谷丰登 */
.wugu-container { width: 800px; padding: 40px; background: rgba(33, 33, 33, 0.95); border: 4px solid #f1c40f; border-radius: 12px; display: flex; flex-direction: column; align-items: center; box-shadow: 0 0 100px rgba(241, 196, 15, 0.2); pointer-events: auto; }
.wugu-title { font-size: 48px; color: #f1c40f; font-family: 'LiSu'; margin-bottom: 10px; text-shadow: 0 0 10px #f1c40f; }
.wugu-tips { color: #ccc; margin-bottom: 30px; font-size: 18px; }
.wugu-cards { display: flex; gap: 30px; justify-content: center; flex-wrap: wrap; }
.wugu-card-item { cursor: pointer; transition: transform 0.2s; }
.wugu-card-item:hover { transform: scale(1.1); box-shadow: 0 0 20px #f1c40f; }

/* 通用弹窗 (军令状) */
.global-response-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(2px); z-index: 9000; display: flex; justify-content: center; align-items: center; pointer-events: none; }
.response-decree { width: 400px; background: linear-gradient(to bottom, #3e2723, #271c19); border: 4px solid #d4af37; border-radius: 8px; box-shadow: 0 0 50px rgba(0,0,0,0.8), inset 0 0 20px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); pointer-events: auto; }
.decree-header { background: #212121; color: #d4af37; padding: 10px; text-align: center; font-family: 'LiSu', serif; font-size: 24px; border-bottom: 1px solid #d4af37; }
.decree-content { padding: 30px 20px; text-align: center; }
.decree-content h3 { color: #f1c40f; margin: 0 0 15px 0; font-size: 28px; text-shadow: 0 2px 4px #000; }
.decree-content p { color: #d7ccc8; font-size: 18px; margin-bottom: 30px; line-height: 1.5; }
.sub-text { font-size: 14px; color: #aaa; margin-top: -20px; margin-bottom: 20px; }
.decree-btns { display: flex; gap: 20px; justify-content: center; }
.btn-decree { padding: 12px 30px; font-size: 18px; font-family: 'LiSu', serif; border: none; border-radius: 4px; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.5); transition: all 0.2s; }
.btn-decree.confirm { background: linear-gradient(to bottom, #2ecc71, #27ae60); color: #fff; border: 1px solid #145a32; }
.btn-decree.confirm:hover { transform: scale(1.05); filter: brightness(1.1); }
.btn-decree.cancel { background: linear-gradient(to bottom, #e74c3c, #c0392b); color: #fff; border: 1px solid #641e16; }
.btn-decree.cancel:hover { transform: scale(1.05); filter: brightness(1.1); }
@keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }

/* 大厅 */
.lobby-view { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; }
.user-profile-bar { position: absolute; top: 20px; right: 20px; display: flex; align-items: center; justify-content: space-between; gap: 15px; background: linear-gradient(to bottom, #3e2723, #271c19); background-image: repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 6px); border: 2px solid #5d4037; border-bottom-color: #d4af37; border-radius: 8px; padding: 8px 12px; min-width: 200px; box-shadow: 0 6px 15px rgba(0,0,0,0.7); z-index: 1000; }
.profile-left { display: flex; align-items: center; gap: 10px; }
.avatar-frame { width: 44px; height: 44px; border-radius: 50%; border: 2px solid #d4af37; overflow: hidden; background: #000; box-shadow: inset 0 0 5px #000; }
.user-avatar-small { width: 100%; height: 100%; object-fit: cover; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-nickname { font-weight: bold; color: #f1c40f; font-size: 16px; font-family: 'LiSu', serif; text-shadow: 0 1px 2px #000; white-space: nowrap; }
.user-account { color: #aaa; font-size: 12px; transform: scale(0.9); transform-origin: left; }
.btn-logout-seal { width: 36px; height: 36px; display: flex; justify-content: center; align-items: center; flex-direction: column; line-height: 0.9; background: #c62828; border: 2px solid #8e0000; border-radius: 4px; color: #fff; font-family: 'LiSu', serif; font-size: 12px; font-weight: bold; cursor: pointer; box-shadow: inset 0 0 5px rgba(0,0,0,0.3); transition: all 0.2s; }
.btn-logout-seal:hover { background: #d32f2f; transform: scale(1.05); }
.btn-logout-seal:active { transform: scale(0.95); background: #b71c1c; }

/* 游戏区 */
.game-container { width: 100%; height: 100vh; display: flex; flex-direction: column; }
.top-bar { height: 40px; background: rgba(30, 20, 10, 0.95); border-bottom: 2px solid #5d4037; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; color: #d7ccc8; box-shadow: 0 2px 10px rgba(0,0,0,0.5); }
.label { color: #8d6e63; margin-right: 5px; font-size: 0.9em; }
.divider { margin: 0 10px; color: #444; }
.btn-wood-small { background: #3e2723; border: 1px solid #5d4037; color: #d7ccc8; padding: 4px 12px; border-radius: 2px; cursor: pointer; font-size: 12px; }
.btn-wood-small:hover { border-color: #d4af37; color: #fff; }
.battlefield { flex: 1; position: relative; display: flex; flex-direction: column; justify-content: space-between; padding: 20px 0; overflow: hidden; }
.opponents-row { display: flex; justify-content: center; gap: 40px; padding-top: 10px; z-index: 10; }
.player-slot { position: relative; display: flex; flex-direction: column; align-items: center; }
.ready-tag { margin-top: 5px; font-size: 12px; padding: 2px 8px; background: #333; border-radius: 4px; color: #aaa; border: 1px solid #555; }
.ready-tag.ok { background: #145a32; color: #2ecc71; border-color: #27ae60; }
.floating-menu { position: absolute; top: 100%; left: 50%; transform: translateX(-50%); width: 140px; background: rgba(33, 33, 33, 0.95); border: 1px solid #f1c40f; border-radius: 4px; box-shadow: 0 5px 20px rgba(0,0,0,0.8); z-index: 2000; overflow: hidden; margin-top: 10px; }
.menu-header { background: #f1c40f; color: #3e2723; font-weight: bold; font-size: 12px; text-align: center; padding: 4px; }
.menu-items { display: flex; flex-direction: column; }
.menu-item { background: transparent; border: none; border-bottom: 1px solid #444; color: #ddd; padding: 8px 10px; text-align: left; cursor: pointer; font-size: 12px; transition: background 0.2s; }
.menu-item:hover { background: #3e2723; color: #f1c40f; }
.menu-item:last-child { border-bottom: none; }
.desk-area { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 600px; height: 200px; display: flex; justify-content: center; align-items: center; }
.played-pile { display: flex; align-items: center; }
.desk-card { margin-right: -50px; transform: scale(0.9); box-shadow: 0 5px 20px rgba(0,0,0,0.6); }
.desk-card:last-child { margin-right: 0; transform: scale(1); z-index: 10; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }

/* 底部控制台 */
.control-panel { height: 220px; background-color: var(--sgs-wood-dark, #3e2723); background-image: repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 10px); border-top: 4px solid #8d6e63; box-shadow: 0 -5px 20px rgba(0,0,0,0.8); display: flex; align-items: flex-end; padding: 15px 40px; position: relative; z-index: 100; }
.my-info-group { display: flex; align-items: flex-end; margin-bottom: 10px; margin-right: 20px; }
.my-avatar-area { transform: scale(1.15); transform-origin: bottom left; margin-right: 15px; }
.my-skills-box { background: rgba(0,0,0,0.3); border: 1px solid #5d4037; border-radius: 4px; padding: 5px; width: 100px; height: 100px; overflow-y: auto; display: flex; flex-direction: column; position: relative; }
.skills-label { font-size: 10px; color: #8d6e63; border-bottom: 1px solid #555; margin-bottom: 4px; text-align: center; }
.skills-list { display: flex; flex-wrap: wrap; gap: 4px; }
.skill-tag { background: #2c3e50; color: #f1c40f; border: 1px solid #f1c40f; font-size: 10px; padding: 2px 4px; border-radius: 2px; cursor: help; font-family: 'LiSu', serif; transition: all 0.2s; }
.skill-tag:hover { background: #f1c40f; color: #2c3e50; }

/* 技能详情弹窗 */
.skill-detail-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 5000;
  display: flex; justify-content: center; align-items: center; backdrop-filter: blur(2px);
}
.skill-detail-card {
  width: 320px; background: rgba(33, 33, 33, 0.95);
  border: 2px solid #f1c40f; border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.8); overflow: hidden;
}
.sd-header {
  background: #2c3e50; color: #f1c40f; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1c40f;
  font-family: 'LiSu'; font-size: 20px;
}
.sd-close { background: none; border: none; color: #aaa; font-size: 24px; cursor: pointer; line-height: 1; }
.sd-close:hover { color: #fff; }
.sd-body { padding: 20px; color: #ddd; font-size: 15px; line-height: 1.6; text-align: left; }

.my-hand-zone { flex: 1; height: 100%; display: flex; align-items: flex-end; overflow: hidden; padding-bottom: 10px; }
.highlight-zone { z-index: 9500 !important; position: relative; } /* 关键：解决遮罩层点击穿透问题 */
.hand-scroll-wrapper { width: 100%; overflow-x: auto; overflow-y: visible; padding-top: 60px; }
.hand-cards-row { display: flex; align-items: flex-end; padding-left: 20px; padding-bottom: 10px; }
.hand-card-item { margin-right: -50px; transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94); transform-origin: bottom center; }
.hand-card-item:hover { transform: translateY(-40px) scale(1.1); z-index: 100; }
.hand-card-item.selected { transform: translateY(-60px) scale(1.1); z-index: 99; box-shadow: 0 0 20px #f1c40f; border-color: #f1c40f; }
.command-zone { width: 160px; height: 100%; display: flex; justify-content: center; align-items: center; background: rgba(0,0,0,0.2); border-left: 2px solid #5d4037; padding-left: 20px; margin-left: 10px; }
.btn-gold-large { font-size: 20px; padding: 10px 20px; width: 100%; background: linear-gradient(to bottom, #f1c40f, #b7950b); border: 1px solid #7d6608; color: #3e2723; font-weight: bold; border-radius: 4px; cursor: pointer; box-shadow: 0 4px 0 #7d6608; font-family: 'LiSu', serif; }
.btn-gold-large:active { transform: translateY(4px); box-shadow: none; }
.btn-wood-large { font-size: 18px; padding: 10px 20px; width: 100%; background: #5d4037; border: 1px solid #3e2723; color: #d7ccc8; border-radius: 4px; cursor: pointer; box-shadow: 0 4px 0 #3e2723; font-family: 'LiSu', serif; }
.btn-wood-large.ready { background: #27ae60; color: #fff; border-color: #145a32; box-shadow: 0 4px 0 #145a32; }
.btn-wood-large:active { transform: translateY(4px); box-shadow: none; }
.turn-indicator { color: #aaa; font-size: 14px; text-align: center; }
.wait-icon { display: block; font-size: 24px; margin-bottom: 5px; }
.my-turn-actions { width: 100%; }
.turn-title { color: #f1c40f; font-size: 18px; text-align: center; margin-bottom: 15px; font-family: 'LiSu'; text-shadow: 0 0 10px #f1c40f; }
.btn-group-vertical { display: flex; flex-direction: column; gap: 10px; }
.btn-action { width: 100%; padding: 10px; font-size: 16px; font-weight: bold; border-radius: 4px; cursor: pointer; font-family: 'LiSu'; }
.btn-action.confirm { background: linear-gradient(to bottom, #c0392b, #922b21); color: #fff; border: 1px solid #641e16; box-shadow: 0 3px 0 #641e16; }
.btn-action.cancel { background: #444; color: #ccc; border: 1px solid #222; box-shadow: 0 3px 0 #222; }
.btn-action:active { transform: translateY(3px); box-shadow: none; }
.btn-action:disabled { filter: grayscale(1); cursor: not-allowed; opacity: 0.6; }
.active-skills-row { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 10px; justify-content: center; }
.btn-skill { background: #2980b9; color: #fff; border: 1px solid #3498db; border-radius: 4px; padding: 4px 8px; font-size: 12px; cursor: pointer; font-family: 'LiSu'; }
.btn-skill:hover { background: #3498db; }
.skill-mode-title { color: #f1c40f; font-size: 14px; margin-bottom: 5px; text-align: center; }
.profile-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 3000; display: flex; justify-content: center; align-items: center; }
.profile-card { background: #2c3e50; width: 320px; padding: 25px; border-radius: 8px; border: 2px solid #95a5a6; box-shadow: 0 0 30px rgba(0,0,0,0.8); }
.profile-header { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; font-size: 22px; font-weight: bold; border-bottom: 1px solid #555; padding-bottom: 10px; }
.p-kingdom { padding: 4px 8px; border-radius: 4px; font-size: 16px; color: #fff; }
.p-kingdom.wei { background: #2980b9; } .p-kingdom.shu { background: #c0392b; } .p-kingdom.wu { background: #27ae60; } .p-kingdom.qun { background: #7f8c8d; }
.p-content { display: flex; gap: 20px; margin-bottom: 25px; }
.p-avatar-large { width: 80px; height: 80px; border-radius: 8px; border: 3px solid #7f8c8d; object-fit: cover; }
.p-info p { margin: 8px 0; color: #bdc3c7; font-size: 14px; }
.p-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-kick { background: #c0392b; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
.btn-close { background: #7f8c8d; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.zoom-enter-active { transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.zoom-enter-from { transform: scale(0); }
.card-pop-enter-active { transition: all 0.5s ease; }
.card-pop-enter-from { opacity: 0; transform: translateY(50px) scale(0.5); }
.hand-enter-active { transition: all 0.4s ease; }
.hand-enter-from { opacity: 0; transform: translateY(100px); }
</style>