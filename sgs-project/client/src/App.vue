<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { socket } from './services/socket';
import { useUserStore } from './stores/userStore'; // 引入用户状态
import GameCard from './components/GameCard.vue';
import PlayerAvatar from './components/PlayerAvatar.vue';
import Login from './components/Login.vue'; // 引入登录组件

// === 0. 用户系统集成 ===
const userStore = useUserStore();

// 监听登录状态：一旦登录成功，带着 Token 连接 Socket
watch(() => userStore.isLoggedIn, (newVal) => {
  if (newVal && userStore.token) {
    socket.auth = { token: userStore.token }; // 注入 Token
    socket.connect();
  } else {
    socket.disconnect(); // 登出断开
  }
});

// === 1. 数据基础状态 ===
const inRoom = ref(false);        
const roomIdInput = ref("101");   
const handCards = ref([]);        
const playedCards = ref([]);      
const players = ref([]);          
const gameState = ref({ 
  phase: 'waiting', 
  current_seat: 0, 
  room_id: '', 
  is_started: false, 
  deck_count: 0,
  pending: null,    // 核心：存储服务器下发的询问动作
  winner_sid: null  // 核心：存储胜利者ID
});
const systemMsg = ref("");        

// === 2. 交互状态控制 ===
const selectedHandIndex = ref(-1);
const selectedTargetSid = ref(null);

// === 3. 计算属性逻辑 ===
const mySid = computed(() => socket.id);
const me = computed(() => players.value.find(p => p.sid === mySid.value));
const isHost = computed(() => me.value?.is_host || false);

// 当前是否轮到我执行“主动出牌”
const isMyTurn = computed(() => {
  if (!players.value.length || gameState.value.pending || gameState.value.phase === 'game_over') return false; 
  const currentP = players.value.find(p => p.seat_id === gameState.value.current_seat);
  return gameState.value.is_started && 
         currentP && 
         currentP.sid === mySid.value && 
         gameState.value.phase === 'play';
});

// 当前我是否需要做出“响应操作”（如：对方杀我，我要选闪）
const isMyResponse = computed(() => {
  return gameState.value.pending && gameState.value.pending.target_sid === mySid.value;
});

// === 4. 生命周期与 Socket 监听 ===
onMounted(() => {
  // 修改：只有已登录才连接，否则等待登录成功
  if (userStore.isLoggedIn && userStore.token) {
    socket.auth = { token: userStore.token };
    socket.connect();
  }

  socket.on('connect_error', (err) => {
    if (err.message === "身份验证失败") {
        showToast("⚠️ 登录已过期，请重新登录");
        userStore.logout();
    }
  });

  socket.on('hand_update', (data) => { 
    handCards.value = data.cards; 
  });

  socket.on('room_update', (data) => {
    console.log("🏠 收到房间数据:", data);
    players.value = data.players;
    gameState.value = data; 
    inRoom.value = true;
  });

  socket.on('kicked', () => {
    resetToLobby();
    showToast("🚫 你已被房主踢出房间");
  });

  socket.on('game_started', () => {
    playedCards.value = [];
    showToast("⚔️ 战火燃起，决战开始！");
  });

  socket.on('player_played', (data) => {
    playedCards.value.push(data.card);
    if (playedCards.value.length > 5) playedCards.value.shift();
    if (data.player_id === socket.id) resetSelection();
  });

  socket.on('system_message', (data) => showToast(data.msg));
});

onUnmounted(() => {
  socket.off();
  socket.disconnect();
});

// === 5. 交互核心方法 ===

// A. 基础操作
const joinRoom = () => { 
  if (roomIdInput.value) socket.emit('join_room', { room_id: roomIdInput.value }); 
};

const toggleReady = () => socket.emit('toggle_ready', {});

const startGame = () => socket.emit('start_game', {});

const endTurn = () => {
  if (gameState.value.pending) return showToast("请先完成当前询问");
  socket.emit('end_turn', {});
};

// B. 返回大厅 (彻底重置)
const resetToLobby = () => {
  socket.emit('leave_room', {}); // 通知后端离开
  inRoom.value = false;
  // 清空所有状态，防止数据污染
  handCards.value = [];
  playedCards.value = [];
  players.value = [];
  gameState.value = { 
    phase: 'waiting', current_seat: 0, room_id: '', 
    is_started: false, deck_count: 0, pending: null, winner_sid: null 
  };
  resetSelection();
};

// C. 主动出牌确认
const confirmPlay = () => {
  if (selectedHandIndex.value === -1) return;
  const card = handCards.value[selectedHandIndex.value];
  
  // 必须选目标的牌：杀、顺手、拆桥
  const needsTarget = ['杀', '顺手牵羊', '过河拆桥'].includes(card.name);
  if (needsTarget && !selectedTargetSid.value) {
    return showToast("⚠️ 请先点击选择一名目标玩家");
  }
  
  socket.emit('play_card', {
    card_index: selectedHandIndex.value,
    target_sid: selectedTargetSid.value
  });
};

// D. 响应询问操作 (出闪、拆牌位置、顺手位置)
const respondAction = (useCardIndex = null, area = null) => {
  socket.emit('respond_action', {
    card_index: useCardIndex,
    target_area: area
  });
  resetSelection();
};

const selectCard = (index) => {
  selectedHandIndex.value = (selectedHandIndex.value === index) ? -1 : index;
};

const selectTarget = (sid) => {
  if (sid === mySid.value) return; 
  selectedTargetSid.value = (selectedTargetSid.value === sid) ? null : sid;
};

const resetSelection = () => {
  selectedHandIndex.value = -1;
  selectedTargetSid.value = null;
};

const showToast = (msg) => {
  systemMsg.value = msg;
  setTimeout(() => { systemMsg.value = ""; }, 3000);
};

// 辅助：检查手牌中是否有闪
const hasShan = computed(() => handCards.value.some(c => c.name === '闪'));
</script>

<template>
  <div class="sgs-app-root">
    <transition name="fade">
      <div v-if="systemMsg" class="app-toast">{{ systemMsg }}</div>
    </transition>

    <transition name="zoom">
      <div v-if="gameState.phase === 'game_over'" class="victory-overlay">
        <div class="victory-modal">
          <h1 class="v-title" :class="{ win: gameState.winner_sid === mySid }">
            {{ gameState.winner_sid === mySid ? '🏆 凯旋归来' : '💀 战死沙场' }}
          </h1>
          <p class="v-info">获胜者: {{ players.find(p => p.sid === gameState.winner_sid)?.seat_id }}号位</p>
          <button class="btn-restart" @click="resetToLobby">回到大厅</button>
        </div>
      </div>
    </transition>

    <Login v-if="!userStore.isLoggedIn" />

    <div v-else-if="!inRoom" class="lobby-view">
      <div class="user-profile-bar">
        <div class="profile-left">
          <img :src="`/avatars/${userStore.user?.avatar || 'default.png'}`" class="user-avatar-small" />
          <div class="user-details">
            <div class="user-nickname">{{ userStore.user?.nickname || '未知武将' }}</div>
            <div class="user-account">@{{ userStore.user?.username }}</div>
          </div>
        </div>
        <button class="btn-logout" @click="userStore.logout()">注销</button>
      </div>

      <div class="lobby-card">
        <h1 class="logo">🏯 三国杀 · 硬核交互版</h1>
        <div class="join-form">
          <input v-model="roomIdInput" placeholder="输入房号" maxlength="6" @keyup.enter="joinRoom">
          <button @click="joinRoom" class="btn-join">进入房间</button>
        </div>
        <p class="lobby-hint">满2人即可开始，房主需确认全员准备</p>
      </div>
    </div>

    <div v-else class="game-view">
      
      <div class="game-header">
        <div class="header-inner">
          <div class="meta-info">房号: {{ gameState.room_id }} | 牌堆: {{ gameState.deck_count }}</div>
          <div class="room-actions">
            <template v-if="!gameState.is_started">
              <button v-if="isHost" class="btn-gold" @click="startGame">🚀 开启战斗</button>
              <button v-else :class="['btn-ready', { active: me?.is_ready }]" @click="toggleReady">准备</button>
            </template>
            <div v-else :class="['turn-box', { active: isMyTurn }]">
              {{ isMyTurn ? '🔥 你的回合' : `等待 ${gameState.current_seat}号位...` }}
            </div>
            <button class="btn-leave" @click="resetToLobby">离开</button>
          </div>
        </div>
      </div>

      <div class="opponents-zone">
        <div class="opponents-wrapper">
          <div v-for="p in players.filter(p => p.sid !== mySid)" :key="p.sid" class="player-slot">
            <PlayerAvatar 
              :player="p"
              :is-current="gameState.current_seat === p.seat_id"
              :is-selected="selectedTargetSid === p.sid"
              @click="selectTarget(p.sid)"
            />

            <div v-if="gameState.pending?.source_sid === mySid && 
                      (gameState.pending?.action_type === 'ask_for_snatch' || gameState.pending?.action_type === 'ask_for_dismantle') &&
                      (gameState.pending?.extra_data.target_to_snatch === p.sid || gameState.pending?.extra_data.target_to_dismantle === p.sid)" 
                 class="interaction-box">
              <div class="box-title">{{ gameState.pending?.action_type === 'ask_for_snatch' ? '顺手牵羊' : '过河拆桥' }}</div>
              <button class="int-btn" @click="respondAction(null, 'hand')">🖐️ 拿手牌</button>
              <button v-if="p.equips.weapon" class="int-btn" @click="respondAction(null, 'weapon')">⚔️ 拿武器</button>
              <button v-if="p.equips.armor" class="int-btn" @click="respondAction(null, 'armor')">🛡️ 拿防具</button>
              <button v-if="p.equips.horse_plus" class="int-btn" @click="respondAction(null, 'horse_plus')">🐎 拿防御马</button>
            </div>

            <div v-if="!gameState.is_started" class="ready-tag" :class="{ ok: p.is_ready }">
              {{ p.is_ready ? '已准备' : '未准备' }}
            </div>
          </div>
        </div>
      </div>

      <div class="board-center">
        <div v-if="isMyResponse && gameState.pending?.action_type === 'ask_for_shan'" class="ask-modal-overlay">
          <div class="ask-card">
            <h3>⚔️ 遭受攻击！</h3>
            <p>对方对你出【杀】，是否响应【闪】？</p>
            <div class="ask-btns">
              <button class="btn-confirm" :disabled="!hasShan" @click="respondAction(handCards.findIndex(c => c.name === '闪'))">出闪</button>
              <button class="btn-cancel" @click="respondAction(null)">不出（掉血）</button>
            </div>
          </div>
        </div>

        <div class="table-surface">
          <div class="surface-label">桌面出牌区</div>
          <transition-group name="card-pop" tag="div" class="played-pile">
            <GameCard v-for="c in playedCards" :key="c.card_id" :card="c" class="desk-card" />
          </transition-group>
        </div>
      </div>

      <div class="bottom-zone">
        <div class="action-console">
          <transition name="fade">
            <div v-if="isMyTurn" class="console-btns">
              <button class="btn-play-action" :disabled="selectedHandIndex === -1" @click="confirmPlay">出牌</button>
              <button class="btn-end-turn" @click="endTurn">结束回合</button>
            </div>
          </transition>
        </div>

        <div class="player-bottom-layout">
          <div class="my-portrait-area">
            <PlayerAvatar :player="me" :is-me="true" :is-current="isMyTurn" />
          </div>

          <div class="my-hand-area">
            <div class="hand-row">
              <transition-group name="hand">
                <GameCard 
                  v-for="(card, index) in handCards" :key="card.card_id" :card="card"
                  :class="{ selected: selectedHandIndex === index }" @click="selectCard(index)"
                />
              </transition-group>
            </div>
          </div>

          <div class="balance-spacer"></div>
        </div>
      </div>

    </div>
  </div>
</template>

<style>
/* 🌟 全局强制样式重置 */
html, body {
  margin: 0 !important;
  padding: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  overflow: hidden !important; 
  background-color: #000;
}

#app {
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
}
</style>

<style scoped>
.sgs-app-root { width: 100%; height: 100%; color: #fff; font-family: "PingFang SC", sans-serif; display: flex; flex-direction: column; }
.app-toast { position: fixed; top: 60px; left: 50%; transform: translateX(-50%); background: #c0392b; padding: 10px 30px; border-radius: 20px; z-index: 10000; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }

/* 胜利大屏 */
.victory-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 9999; display: flex; justify-content: center; align-items: center; }
.victory-modal { background: #111; padding: 60px; border: 2px solid #f1c40f; border-radius: 20px; text-align: center; }
.v-title { font-size: 4em; margin-bottom: 20px; color: #7f8c8d; }
.v-title.win { color: #f1c40f; text-shadow: 0 0 20px #f1c40f; }
.btn-restart { margin-top: 30px; padding: 12px 40px; background: #f1c40f; border: none; font-weight: bold; cursor: pointer; border-radius: 5px; color: #000; }

/* 大厅 */
.lobby-view { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; background: radial-gradient(circle, #2c3e50, #000); position: relative; }

/* === 用户信息栏 (新增) === */
.user-profile-bar {
  position: absolute; top: 20px; right: 20px;
  display: flex; align-items: center; gap: 15px;
  background: rgba(255,255,255,0.1); padding: 10px 20px; border-radius: 50px;
  border: 1px solid rgba(255,255,255,0.2);
  backdrop-filter: blur(5px);
}
.user-avatar-small { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #d4af37; object-fit: cover; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-nickname { font-weight: bold; color: #f1c40f; font-size: 14px; }
.user-account { color: #aaa; font-size: 12px; }
.btn-logout { background: transparent; border: 1px solid #c0392b; color: #c0392b; padding: 5px 12px; border-radius: 20px; cursor: pointer; font-size: 12px; transition: all 0.2s; }
.btn-logout:hover { background: #c0392b; color: #fff; }

.lobby-card { background: rgba(255, 255, 255, 0.05); padding: 50px; border-radius: 20px; border: 1px solid #333; text-align: center; }
.logo { margin-bottom: 30px; letter-spacing: 4px; }
.join-form { display: flex; gap: 10px; }
.join-form input { padding: 12px; border: none; border-radius: 5px; width: 120px; text-align: center; font-size: 1.1em; }
.btn-join { padding: 12px 24px; background: #27ae60; border: none; border-radius: 5px; color: #fff; cursor: pointer; font-size: 1.1em; }

/* 游戏板 */
.game-view { flex: 1; display: flex; flex-direction: column; position: relative; }
.game-header { height: 50px; background: rgba(0,0,0,0.8); border-bottom: 1px solid #333; display: flex; justify-content: center; }
.header-inner { width: 95%; max-width: 1400px; display: flex; justify-content: space-between; align-items: center; }
.btn-gold { background: #e67e22; border: none; color: #fff; padding: 8px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-ready { background: #34495e; border: none; color: #aaa; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
.btn-ready.active { background: #27ae60; color: #fff; }
.btn-leave { background: #555; border: none; padding: 4px 12px; color: #fff; border-radius: 4px; cursor: pointer; margin-left: 10px; }
.turn-box.active { color: #f1c40f; font-weight: bold; text-shadow: 0 0 10px rgba(241,196,15,0.5); }

/* 对手 */
.opponents-zone { height: 170px; display: flex; justify-content: center; padding-top: 15px; }
.opponents-wrapper { display: flex; gap: 40px; }
.player-slot { position: relative; display: flex; flex-direction: column; align-items: center; }

/* 🌟 核心：抢牌选择框 */
.interaction-box { 
  position: absolute; bottom: -85px; width: 90px; 
  display: flex; flex-direction: column; gap: 2px; 
  z-index: 100; background: rgba(0,0,0,0.9); padding: 5px; border-radius: 4px; border: 1px solid #f39c12;
}
.box-title { font-size: 10px; color: #f39c12; text-align: center; margin-bottom: 2px; }
.int-btn { font-size: 10px; background: #f39c12; color: #000; border: none; padding: 2px; cursor: pointer; font-weight: bold; }

.ready-tag { margin-top: 5px; font-size: 11px; padding: 2px 8px; background: #444; border-radius: 10px; }
.ready-tag.ok { background: #27ae60; }

/* 中心桌面 */
.board-center { flex: 1; display: flex; justify-content: center; align-items: center; position: relative; }
.ask-modal-overlay { position: absolute; z-index: 500; background: rgba(0,0,0,0.8); width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; }
.ask-card { background: #111; padding: 30px; border: 2px solid #e67e22; border-radius: 15px; text-align: center; }
.ask-btns { display: flex; gap: 20px; margin-top: 20px; }
.btn-confirm { background: #27ae60; color: #fff; border: none; padding: 10px 30px; font-weight: bold; cursor: pointer; }
.btn-confirm:disabled { background: #555; cursor: not-allowed; }
.btn-cancel { background: #c0392b; color: #fff; border: none; padding: 10px 30px; cursor: pointer; }

.table-surface { width: 75%; height: 200px; background: rgba(255,255,255,0.02); border-radius: 100px; border: 1px dashed #333; display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; }
.surface-label { position: absolute; top: 10px; font-size: 11px; color: #444; letter-spacing: 5px; }
.played-pile { display: flex; gap: 10px; }
.desk-card { transform: scale(0.85); box-shadow: 0 10px 20px rgba(0,0,0,0.5); }

/* 底部区域 */
.bottom-zone { height: 270px; display: flex; flex-direction: column; align-items: center; background: linear-gradient(transparent, #000); }
.action-console { height: 60px; display: flex; align-items: center; }
.btn-play-action { background: #c0392b; color: #fff; border: none; padding: 12px 60px; border-radius: 30px; font-size: 1.2em; font-weight: bold; cursor: pointer; box-shadow: 0 4px #922b21; }
.btn-play-action:disabled { background: #444; box-shadow: none; color: #777; cursor: not-allowed; }
.btn-end-turn { background: #34495e; color: #fff; border: none; padding: 10px 25px; border-radius: 20px; cursor: pointer; margin-left: 10px; }

.player-bottom-layout { width: 95%; max-width: 1400px; display: flex; align-items: flex-end; padding-bottom: 20px; }
.my-portrait-area { width: 120px; flex-shrink: 0; }
.balance-spacer { width: 120px; flex-shrink: 0; } 

.my-hand-area { flex: 1; display: flex; justify-content: center; overflow: visible; }
.hand-row { display: flex; padding-left: 60px; } 
.hand-row .card {
  margin-left: -60px;
  transition: 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform-origin: bottom center;
}
.hand-row .card:first-child { margin-left: 0; }
.hand-row .card:hover { transform: translateY(-30px) scale(1.1); z-index: 100; }
.hand-row .card.selected { transform: translateY(-60px) scale(1.05); border-color: #f1c40f; z-index: 99; box-shadow: 0 0 20px rgba(241,196,15,0.5); }

/* 动画库 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.zoom-enter-active { transition: transform 0.5s ease; }
.zoom-enter-from { transform: scale(0); }
.card-pop-enter-active { transition: all 0.5s ease; }
.card-pop-enter-from { opacity: 0; transform: translateY(30px) scale(0.6); }
.hand-enter-active { transition: all 0.4s ease; }
.hand-enter-from { opacity: 0; transform: translateY(100px); }
</style>