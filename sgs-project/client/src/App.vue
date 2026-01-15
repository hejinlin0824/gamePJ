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
const selectedHandIndex = ref(-1);
const selectedTargetSid = ref(null);

// 控制个人信息/踢人弹窗
const showProfileModal = ref(false);
const currentProfile = ref(null);

// === 3. 计算属性逻辑 ===
const mySid = computed(() => socket.id);
const me = computed(() => players.value.find(p => p.sid === mySid.value));
const isHost = computed(() => me.value?.is_host || false);

// 判断是否轮到我出牌
const isMyTurn = computed(() => {
  if (!players.value.length || gameState.value.pending || gameState.value.phase === 'game_over') return false; 
  const currentP = players.value.find(p => p.seat_id === gameState.value.current_seat);
  return gameState.value.is_started && 
         currentP && 
         currentP.sid === mySid.value && 
         gameState.value.phase === 'play';
});

// 判断是否轮到我响应
const isMyResponse = computed(() => {
  return gameState.value.pending && gameState.value.pending.target_sid === mySid.value;
});

// 选将阶段
const showGeneralSelector = computed(() => {
  return gameState.value.phase === 'pick_general' && me.value && !me.value.general_id; 
});
const isWaitingOthers = computed(() => {
  return gameState.value.phase === 'pick_general' && me.value && me.value.general_id;
});

const hasShan = computed(() => handCards.value.some(c => c.name === '闪'));

// === 4. 生命周期与 Socket 监听 ===
onMounted(() => {
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

const joinRoom = (roomId) => { 
  socket.emit('join_room', { room_id: roomId }); 
};

const toggleReady = () => socket.emit('toggle_ready', {});

const startGame = () => socket.emit('start_game', {});

const onSelectGeneral = (genId) => {
  socket.emit('select_general', { general_id: genId });
};

const endTurn = () => {
  if (gameState.value.pending) return showToast("请先完成当前询问");
  socket.emit('end_turn', {});
};

const resetToLobby = () => {
  socket.emit('leave_room', {}); 
  inRoom.value = false;
  socket.emit('get_lobby', {});
  
  handCards.value = [];
  playedCards.value = [];
  players.value = [];
  gameState.value = { 
    phase: 'waiting', current_seat: 0, room_id: '', 
    is_started: false, deck_count: 0, pending: null, winner_sid: null 
  };
  resetSelection();
};

const confirmPlay = () => {
  if (selectedHandIndex.value === -1) return;
  const card = handCards.value[selectedHandIndex.value];
  
  const needsTarget = ['杀', '顺手牵羊', '过河拆桥', '决斗'].includes(card.name);
  if (needsTarget && !selectedTargetSid.value) {
    return showToast("⚠️ 请先点击选择一名目标玩家");
  }
  
  socket.emit('play_card', {
    card_index: selectedHandIndex.value,
    target_sid: selectedTargetSid.value
  });
};

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

// 头像点击逻辑
const handleAvatarClick = (player) => {
  if (gameState.value.is_started && (isMyTurn.value || isMyResponse.value)) {
    selectTarget(player.sid);
  } else {
    openProfile(player);
  }
};

const openProfile = (player) => {
  currentProfile.value = player;
  showProfileModal.value = true;
};

const closeProfile = () => {
  showProfileModal.value = false;
  currentProfile.value = null;
};

const kickCurrentPlayer = () => {
  if (currentProfile.value) {
    socket.emit('kick_player', { target_sid: currentProfile.value.sid });
    closeProfile();
  }
};
</script>

<template>
  <div class="sgs-app-root">
    
    <transition name="fade">
      <div v-if="systemMsg" class="app-toast">
        <div class="toast-content">📜 {{ systemMsg }}</div>
      </div>
    </transition>

    <transition name="zoom">
      <GeneralSelector 
        v-if="showGeneralSelector" 
        :candidates="me?.candidates || []"
        @select="onSelectGeneral"
      />
    </transition>

    <transition name="fade">
      <div v-if="isWaitingOthers" class="waiting-overlay-full">
        <div class="waiting-text">
          <div class="spinner"></div>
          正在等待其他诸侯点将...
        </div>
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
            <button 
              v-if="isHost && currentProfile.sid !== mySid && !gameState.is_started" 
              class="btn-kick" 
              @click="kickCurrentPlayer"
            >
              👢 踢出房间
            </button>
            <button class="btn-close" @click="closeProfile">关闭</button>
          </div>
        </div>
      </div>
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
      <RoomList @join="joinRoom" />
    </div>

    <div v-else class="game-container">
      
      <div class="top-bar">
        <div class="room-info">
          <span class="label">战场:</span> {{ gameState.room_id }}号营 
          <span class="divider">|</span>
          <span class="label">剩余牌堆:</span> {{ gameState.deck_count }}
        </div>
        <div class="top-actions">
          <button class="btn-wood-small" @click="resetToLobby">撤退</button>
        </div>
      </div>

      <div class="battlefield">
        <div class="opponents-row">
          <div v-for="p in players.filter(p => p.sid !== mySid)" :key="p.sid" class="player-slot">
            <PlayerAvatar 
              :player="p" 
              :is-current="gameState.current_seat === p.seat_id"
              :is-selected="selectedTargetSid === p.sid"
              @click="handleAvatarClick(p)" 
            />
            
            <div v-if="!gameState.is_started" class="ready-tag" :class="{ ok: p.is_ready }">
              {{ p.is_ready ? '已准备' : '未准备' }}
            </div>

            <div v-if="gameState.pending?.source_sid === mySid && 
                       (gameState.pending?.action_type === 'ask_for_snatch' || gameState.pending?.action_type === 'ask_for_dismantle') &&
                       (gameState.pending?.extra_data.target_to_snatch === p.sid || gameState.pending?.extra_data.target_to_dismantle === p.sid)" 
                 class="interaction-menu">
               <div class="menu-title">{{ gameState.pending?.action_type === 'ask_for_snatch' ? '顺手牵羊' : '过河拆桥' }}</div>
               <button class="menu-btn" @click="respondAction(null, 'hand')">🖐️ 拿手牌</button>
               <button v-if="p.equips.weapon" class="menu-btn" @click="respondAction(null, 'weapon')">⚔️ 卸武器</button>
               <button v-if="p.equips.armor" class="menu-btn" @click="respondAction(null, 'armor')">🛡️ 卸防具</button>
               <button v-if="p.equips.horse_plus" class="menu-btn" @click="respondAction(null, 'horse_plus')">🐎 卸防御马</button>
               <button v-if="p.equips.horse_minus" class="menu-btn" @click="respondAction(null, 'horse_minus')">🐎 卸进攻马</button>
            </div>
          </div>
        </div>

        <div class="desk-area">
          <transition-group name="card-pop" tag="div" class="played-pile">
            <GameCard v-for="c in playedCards" :key="c.card_id" :card="c" class="desk-card" />
          </transition-group>
          <div v-if="isMyResponse" class="response-modal">
             <div v-if="gameState.pending?.action_type === 'ask_for_skill_confirm'" class="response-inner">
                <h3>⚔️ 技能发动确认</h3>
                <p>是否发动【{{ gameState.pending.extra_data.skill_name }}】<br>将牌转化为【{{ gameState.pending.extra_data.transform_name }}】？</p>
                <div class="btn-group">
                  <button class="btn-confirm" @click="respondAction(null, 'use_skill')">确认发动</button>
                  <button class="btn-cancel" @click="respondAction(null, 'cancel')">取消</button>
                </div>
             </div>
             <div v-else-if="gameState.pending?.action_type === 'ask_for_shan'" class="response-inner">
                <h3>🛡️ 敌军杀来！</h3>
                <p>请打出一张【闪】</p>
                <div class="btn-group">
                  <button class="btn-confirm" @click="respondAction(handCards.findIndex(c => c.name === '闪'))">出闪 {{ hasShan ? '' : '(转化)' }}</button>
                  <button class="btn-cancel" @click="respondAction(null)">放弃 (掉血)</button>
                </div>
             </div>
          </div>
        </div>
      </div>

      <div class="control-panel">
        
        <div class="my-avatar-area">
          <PlayerAvatar :player="me" :is-me="true" :is-current="isMyTurn" />
        </div>

        <div class="my-hand-zone">
          <div class="hand-scroll-wrapper">
            <transition-group name="hand" tag="div" class="hand-cards-row">
              <GameCard 
                v-for="(card, index) in handCards" :key="card.card_id" :card="card"
                class="hand-card-item"
                :class="{ selected: selectedHandIndex === index }" 
                @click="selectCard(index)"
              />
            </transition-group>
          </div>
        </div>

        <div class="command-zone">
          <div v-if="!gameState.is_started" class="pre-game-btns">
             <button v-if="isHost" class="btn-gold-large" @click="startGame">点兵出征</button>
             <button v-else class="btn-wood-large" :class="{ ready: me?.is_ready }" @click="toggleReady">
               {{ me?.is_ready ? '已备战' : '整备' }}
             </button>
          </div>

          <div v-else class="combat-controls">
            <div class="turn-indicator" v-if="!isMyTurn">
              <span class="wait-icon">⏳</span> 
              <span>等待 {{ gameState.current_seat }}号位</span>
            </div>
            <div v-else class="my-turn-actions">
              <div class="turn-title">🔥 你的回合</div>
              <div class="btn-group-vertical">
                <button class="btn-action confirm" :disabled="selectedHandIndex === -1" @click="confirmPlay">出牌</button>
                <button class="btn-action cancel" @click="endTurn">结束回合</button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* === 基础容器 === */
.sgs-app-root { 
  width: 100%; height: 100%; color: #fff; display: flex; flex-direction: column; 
}

/* === 全局 Toast === */
.app-toast {
  position: fixed; top: 15%; left: 50%; transform: translateX(-50%); z-index: 9999; pointer-events: none;
}
.toast-content {
  background: rgba(0, 0, 0, 0.9);
  color: #f1c40f;
  padding: 15px 40px;
  border-radius: 4px;
  border: 2px solid #8d6e63;
  font-size: 20px;
  font-family: 'LiSu', serif;
  box-shadow: 0 10px 30px rgba(0,0,0,0.8);
  text-shadow: 0 2px 4px #000;
}

/* === 加载遮罩 === */
.waiting-overlay-full {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 999;
  display: flex; justify-content: center; align-items: center;
}
.waiting-text {
  font-size: 24px; color: #d4af37; display: flex; flex-direction: column; align-items: center; gap: 20px; font-family: 'LiSu', serif;
}
.spinner {
  width: 50px; height: 50px; border: 4px solid rgba(212,175,55,0.2); border-top-color: #d4af37; border-radius: 50%; animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* === 胜利结算 === */
.victory-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 9999; display: flex; justify-content: center; align-items: center; }
.victory-modal { background: #111; padding: 50px 80px; border: 4px solid #f1c40f; border-radius: 12px; text-align: center; box-shadow: 0 0 50px rgba(241, 196, 15, 0.3); }
.v-title { font-size: 5em; margin: 0 0 20px 0; color: #7f8c8d; font-family: 'LiSu', serif; }
.v-title.win { 
  color: #f1c40f; 
  text-shadow: 0 0 20px #f1c40f, 0 0 40px #e67e22;
  background: linear-gradient(to bottom, #fff, #f1c40f, #e67e22);
  -webkit-background-clip: text; color: transparent;
}
.v-info { color: #aaa; font-size: 1.5em; margin-bottom: 30px; }
.btn-restart { padding: 12px 40px; background: #f1c40f; border: none; font-weight: bold; cursor: pointer; border-radius: 4px; color: #3e2723; font-size: 1.2em; }

/* === 大厅视图 === */
.lobby-view { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; }
.user-profile-bar {
  position: absolute; top: 20px; right: 20px;
  display: flex; align-items: center; gap: 15px;
  background: rgba(62, 39, 35, 0.8); padding: 8px 20px; border-radius: 50px;
  border: 1px solid #8d6e63;
  box-shadow: 0 4px 10px rgba(0,0,0,0.5);
}
.user-avatar-small { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #d4af37; object-fit: cover; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-nickname { font-weight: bold; color: #f1c40f; font-size: 14px; }
.user-account { color: #aaa; font-size: 12px; }
.btn-logout { background: transparent; border: 1px solid #c0392b; color: #c0392b; padding: 4px 12px; border-radius: 20px; cursor: pointer; font-size: 12px; }
.btn-logout:hover { background: #c0392b; color: #fff; }

/* === 游戏容器 === */
.game-container {
  width: 100%; height: 100vh; display: flex; flex-direction: column;
}

/* 顶部条 */
.top-bar {
  height: 40px;
  background: rgba(30, 20, 10, 0.95);
  border-bottom: 2px solid #5d4037;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 20px; color: #d7ccc8;
  box-shadow: 0 2px 10px rgba(0,0,0,0.5);
}
.label { color: #8d6e63; margin-right: 5px; font-size: 0.9em; }
.divider { margin: 0 10px; color: #444; }
.btn-wood-small {
  background: #3e2723; border: 1px solid #5d4037; color: #d7ccc8;
  padding: 4px 12px; border-radius: 2px; cursor: pointer; font-size: 12px;
}
.btn-wood-small:hover { border-color: #d4af37; color: #fff; }

/* 中间战场 */
.battlefield {
  flex: 1; position: relative; display: flex; flex-direction: column; justify-content: space-between; padding: 20px 0; overflow: hidden;
}
.opponents-row {
  display: flex; justify-content: center; gap: 40px; padding-top: 10px; z-index: 10;
}
.player-slot { position: relative; display: flex; flex-direction: column; align-items: center; }

/* 准备标签 */
.ready-tag { 
  margin-top: 5px; font-size: 12px; padding: 2px 8px; background: #333; border-radius: 4px; color: #aaa; border: 1px solid #555;
}
.ready-tag.ok { background: #145a32; color: #2ecc71; border-color: #27ae60; }

/* 交互菜单 */
.interaction-menu {
  position: absolute; top: 100%; width: 100px;
  background: rgba(0,0,0,0.9); border: 1px solid #f39c12; border-radius: 4px;
  padding: 5px; z-index: 100; display: flex; flex-direction: column; gap: 4px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.8);
}
.menu-title { font-size: 12px; color: #f39c12; text-align: center; border-bottom: 1px solid #555; padding-bottom: 2px; margin-bottom: 2px; }
.menu-btn { font-size: 11px; background: #333; color: #fff; border: 1px solid #555; cursor: pointer; padding: 4px; text-align: left; }
.menu-btn:hover { background: #f39c12; color: #000; }

/* 桌面区域 */
.desk-area {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 600px; height: 200px; display: flex; justify-content: center; align-items: center;
}
.played-pile { display: flex; align-items: center; }
.desk-card { margin-right: -50px; transform: scale(0.9); box-shadow: 0 5px 20px rgba(0,0,0,0.6); }
.desk-card:last-child { margin-right: 0; transform: scale(1); z-index: 10; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }

/* 响应弹窗 */
.response-modal {
  position: absolute; bottom: 100%; margin-bottom: 20px;
  background: rgba(30, 20, 10, 0.95); border: 2px solid #d4af37; padding: 20px; border-radius: 8px;
  text-align: center; box-shadow: 0 0 30px rgba(212,175,55,0.4); animation: popUp 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes popUp { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.response-inner h3 { margin: 0 0 10px 0; color: #f1c40f; font-family: 'LiSu'; font-size: 24px; }
.response-inner p { color: #d7ccc8; margin-bottom: 15px; }
.btn-group { display: flex; gap: 10px; justify-content: center; }
.btn-confirm { background: #27ae60; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-cancel { background: #c0392b; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }

/* === 底部控制台 (木纹) === */
.control-panel {
  height: 220px;
  background-color: var(--sgs-wood-dark, #3e2723);
  /* 复杂的木纹CSS图案 */
  background-image: repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 10px);
  border-top: 4px solid #8d6e63;
  box-shadow: 0 -5px 20px rgba(0,0,0,0.8);
  display: flex; align-items: flex-end; padding: 15px 40px; position: relative; z-index: 100;
}

/* 自己的头像 */
.my-avatar-area {
  margin-bottom: 10px; margin-right: 20px; transform: scale(1.15); transform-origin: bottom left;
}

/* 手牌区 */
.my-hand-zone {
  flex: 1; height: 100%; display: flex; align-items: flex-end; overflow: hidden; padding-bottom: 10px;
}
.hand-scroll-wrapper {
  width: 100%; overflow-x: auto; overflow-y: visible; padding-top: 40px; /* 留出卡牌浮动空间 */
}
.hand-cards-row {
  display: flex; align-items: flex-end; padding-left: 20px; padding-bottom: 10px;
}
.hand-card-item {
  margin-right: -55px; /* 紧凑堆叠 */
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  transform-origin: bottom center;
}
.hand-card-item:hover {
  transform: translateY(-40px) scale(1.1); z-index: 100;
}
.hand-card-item.selected {
  transform: translateY(-60px) scale(1.1); z-index: 99;
  box-shadow: 0 0 20px #f1c40f;
  border-color: #f1c40f;
}

/* 按钮命令区 */
.command-zone {
  width: 160px; height: 100%;
  display: flex; justify-content: center; align-items: center;
  background: rgba(0,0,0,0.2); border-left: 2px solid #5d4037; padding-left: 20px; margin-left: 10px;
}

.btn-gold-large {
  font-size: 20px; padding: 10px 20px; width: 100%;
  background: linear-gradient(to bottom, #f1c40f, #b7950b);
  border: 1px solid #7d6608; color: #3e2723; font-weight: bold;
  border-radius: 4px; cursor: pointer; box-shadow: 0 4px 0 #7d6608;
  font-family: 'LiSu', serif;
}
.btn-gold-large:active { transform: translateY(4px); box-shadow: none; }

.btn-wood-large {
  font-size: 18px; padding: 10px 20px; width: 100%;
  background: #5d4037; border: 1px solid #3e2723; color: #d7ccc8;
  border-radius: 4px; cursor: pointer; box-shadow: 0 4px 0 #3e2723;
  font-family: 'LiSu', serif;
}
.btn-wood-large.ready { background: #27ae60; color: #fff; border-color: #145a32; box-shadow: 0 4px 0 #145a32; }
.btn-wood-large:active { transform: translateY(4px); box-shadow: none; }

.turn-indicator { color: #aaa; font-size: 14px; text-align: center; }
.wait-icon { display: block; font-size: 24px; margin-bottom: 5px; }

.my-turn-actions { width: 100%; }
.turn-title { color: #f1c40f; font-size: 18px; text-align: center; margin-bottom: 15px; font-family: 'LiSu'; text-shadow: 0 0 10px #f1c40f; }
.btn-group-vertical { display: flex; flex-direction: column; gap: 10px; }
.btn-action {
  width: 100%; padding: 10px; font-size: 16px; font-weight: bold; border-radius: 4px; cursor: pointer; font-family: 'LiSu';
}
.btn-action.confirm {
  background: linear-gradient(to bottom, #c0392b, #922b21); color: #fff; border: 1px solid #641e16; box-shadow: 0 3px 0 #641e16;
}
.btn-action.cancel {
  background: #444; color: #ccc; border: 1px solid #222; box-shadow: 0 3px 0 #222;
}
.btn-action:active { transform: translateY(3px); box-shadow: none; }
.btn-action:disabled { filter: grayscale(1); cursor: not-allowed; opacity: 0.6; }

/* 个人信息弹窗样式 (复用之前的逻辑，这里只微调样式以匹配主题) */
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

/* 动画定义 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.zoom-enter-active { transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.zoom-enter-from { transform: scale(0); }
.card-pop-enter-active { transition: all 0.5s ease; }
.card-pop-enter-from { opacity: 0; transform: translateY(50px) scale(0.5); }
.hand-enter-active { transition: all 0.4s ease; }
.hand-enter-from { opacity: 0; transform: translateY(100px); }
</style>