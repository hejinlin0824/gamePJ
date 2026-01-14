<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { socket } from './services/socket';
import GameCard from './components/GameCard.vue';
import PlayerAvatar from './components/PlayerAvatar.vue';

// === 1. 数据状态 (保持完整逻辑) ===
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
  deck_count: 0 
});
const systemMsg = ref("");        
const selectedHandIndex = ref(-1);
const selectedTargetSid = ref(null);

// === 2. 计算属性 ===
const mySid = computed(() => socket.id);
const me = computed(() => players.value.find(p => p.sid === mySid.value));
const isHost = computed(() => me.value?.is_host || false);

// 判断是否是我的回合且在出牌阶段
const isMyTurn = computed(() => {
  if (!players.value.length) return false;
  const currentP = players.value.find(p => p.seat_id === gameState.value.current_seat);
  return gameState.value.is_started && 
         currentP && 
         currentP.sid === mySid.value && 
         gameState.value.phase === 'play';
});

// === 3. 事件监听 ===
onMounted(() => {
  socket.connect();

  // 全量更新手牌
  socket.on('hand_update', (d) => { 
    handCards.value = d.cards; 
  });

  // 接收房间状态更新 (包括房主、准备状态等)
  socket.on('room_update', (d) => { 
    players.value = d.players; 
    gameState.value = d; 
    inRoom.value = true; 
  });

  // 监听被踢出房间
  socket.on('kicked', () => { 
    inRoom.value = false; 
    handCards.value = [];
    players.value = [];
    systemMsg.value = "🚫 你已被房主踢出房间"; 
    setTimeout(() => systemMsg.value = "", 3000);
  });

  // 游戏开始重置桌面
  socket.on('game_started', () => { 
    playedCards.value = []; 
  });

  // 监听出牌动作
  socket.on('player_played', (d) => {
    playedCards.value.push(d.card);
    if (playedCards.value.length > 5) playedCards.value.shift();
    // 如果是我出的，重置选中状态
    if (d.player_id === socket.id) { 
      selectedHandIndex.value = -1; 
      selectedTargetSid.value = null; 
    }
  });

  // 系统消息提示
  socket.on('system_message', (d) => { 
    systemMsg.value = d.msg; 
    setTimeout(() => systemMsg.value = "", 3000); 
  });
});

onUnmounted(() => { 
  socket.off(); 
  socket.disconnect(); 
});

// === 4. 交互方法 ===
const joinRoom = () => {
  if (roomIdInput.value) socket.emit('join_room', { room_id: roomIdInput.value });
};

const toggleReady = () => socket.emit('toggle_ready', {});

const kickPlayer = (sid) => socket.emit('kick_player', { target_sid: sid });

const startGame = () => socket.emit('start_game', {});

const endTurn = () => socket.emit('end_turn', {});

const confirmPlay = () => {
  if (selectedHandIndex.value === -1) return;
  const card = handCards.value[selectedHandIndex.value];
  if (card?.name === '杀' && !selectedTargetSid.value) {
    systemMsg.value = "⚠️ 请选择目标";
    setTimeout(() => systemMsg.value = "", 2000);
    return;
  }
  socket.emit('play_card', { 
    card_index: selectedHandIndex.value, 
    target_sid: selectedTargetSid.value 
  });
};

const selectCard = (i) => {
  selectedHandIndex.value = (selectedHandIndex.value === i) ? -1 : i;
};

const selectTarget = (sid) => {
  if (sid !== mySid.value) {
    selectedTargetSid.value = (selectedTargetSid.value === sid) ? null : sid;
  }
};
</script>

<template>
  <div class="sgs-root-layout">
    <transition name="fade">
      <div v-if="systemMsg" class="toast-message">{{ systemMsg }}</div>
    </transition>

    <div v-if="!inRoom" class="lobby-view">
      <div class="lobby-box">
        <h1 class="lobby-title">🏯 三国杀 · 联机版</h1>
        <div class="lobby-form">
          <input v-model="roomIdInput" placeholder="输入房间号" maxlength="6" @keyup.enter="joinRoom">
          <button @click="joinRoom">进入房间</button>
        </div>
      </div>
    </div>

    <div v-else class="board-view">
      <div class="header-bar">
        <div class="header-content">
          <div class="game-meta">房间: {{ gameState.room_id }} | 牌堆: {{ gameState.deck_count }}</div>
          
          <div class="room-actions">
            <template v-if="!gameState.is_started">
              <button v-if="isHost" class="btn-primary" @click="startGame">🚀 开始游戏</button>
              <button v-else :class="['btn-ready', {active: me?.is_ready}]" @click="toggleReady">
                {{ me?.is_ready ? '取消准备' : '准备就绪' }}
              </button>
            </template>
            <template v-else>
              <div :class="['turn-indicator', {mine: isMyTurn}]">
                {{ isMyTurn ? '🔥 你的回合' : `等待 ${gameState.current_seat}号位出牌` }}
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="opponents-zone">
        <div class="players-flex">
          <div v-for="p in players.filter(p => p.sid !== mySid)" :key="p.sid" class="opponent-item">
            <button v-if="isHost && !gameState.is_started" class="kick-button" @click.stop="kickPlayer(p.sid)">踢出</button>
            
            <PlayerAvatar 
              :player="p"
              :is-current="gameState.current_seat === p.seat_id"
              :is-selected="selectedTargetSid === p.sid"
              @click="selectTarget(p.sid)"
            />
            
            <div v-if="!gameState.is_started" :class="['ready-status', {done: p.is_ready}]">
              {{ p.is_host ? '房主' : (p.is_ready ? '已准备' : '未准备') }}
            </div>
          </div>
        </div>
      </div>

      <div class="center-zone">
        <div class="table-felt">
          <span class="felt-label">桌面出牌区</span>
          <transition-group name="list" tag="div" class="played-cards-stack">
            <GameCard v-for="c in playedCards" :key="c.card_id" :card="c" class="table-card" />
          </transition-group>
        </div>
      </div>

      <div class="footer-zone">
        <div class="action-dock" v-if="isMyTurn">
          <button class="btn-play" :disabled="selectedHandIndex === -1" @click="confirmPlay">出牌</button>
          <button class="btn-end" @click="endTurn">结束回合</button>
        </div>

        <div class="player-bottom-layout">
          <div class="my-avatar-box">
            <PlayerAvatar :player="me" :is-me="true" :is-current="isMyTurn" />
          </div>

          <div class="hand-cards-box">
            <div class="hand-row">
              <transition-group name="hand">
                <GameCard 
                  v-for="(card, index) in handCards" 
                  :key="card.card_id" 
                  :card="card"
                  :class="{selected: selectedHandIndex === index}"
                  @click="selectCard(index)"
                />
              </transition-group>
            </div>
          </div>

          <div class="avatar-spacer"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* 🌟 核心修复：强制重置全局样式，解决歪掉的问题 */
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
/* 根容器布局 */
.sgs-root-layout {
  width: 100%;
  height: 100%;
  color: #fff;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  display: flex;
  flex-direction: column;
}

/* 提示框 */
.toast-message {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(230, 126, 34, 0.9);
  padding: 8px 24px;
  border-radius: 20px;
  z-index: 9999;
  box-shadow: 0 4px 15px rgba(0,0,0,0.5);
}

/* 场景1：大厅样式 */
.lobby-view {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: radial-gradient(circle at center, #2c3e50 0%, #000 100%);
}
.lobby-box {
  background: rgba(255, 255, 255, 0.05);
  padding: 60px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  backdrop-filter: blur(10px);
}
.lobby-title { margin-bottom: 30px; letter-spacing: 4px; }
.lobby-form { display: flex; gap: 10px; }
.lobby-form input { padding: 12px; border-radius: 6px; border: none; font-size: 1.1em; width: 140px; text-align: center; }
.lobby-form button { padding: 12px 24px; background: #27ae60; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 1.1em; }

/* 场景2：牌桌样式 */
.board-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

/* 顶部栏 */
.header-bar {
  height: 60px;
  background: rgba(0, 0, 0, 0.85);
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: center;
}
.header-content {
  width: 95%;
  max-width: 1400px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.btn-primary { background: #e67e22; color: #fff; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-ready { background: #34495e; color: #ccc; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
.btn-ready.active { background: #27ae60; color: #fff; }
.turn-indicator.mine { color: #f1c40f; font-weight: bold; text-shadow: 0 0 10px rgba(241, 196, 15, 0.5); }

/* 对手区 */
.opponents-zone {
  height: 180px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 20px;
}
.players-flex { display: flex; gap: 40px; }
.opponent-item { position: relative; display: flex; flex-direction: column; align-items: center; }
.kick-button { position: absolute; top: -20px; background: #c0392b; color: #fff; border: none; border-radius: 3px; font-size: 10px; padding: 2px 6px; cursor: pointer; z-index: 10; }
.ready-status { margin-top: 8px; font-size: 12px; background: #444; padding: 2px 8px; border-radius: 10px; }
.ready-status.done { background: #2ecc71; }

/* 出牌区桌面 */
.center-zone {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}
.table-felt {
  width: 80%;
  height: 220px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 110px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
}
.felt-label { position: absolute; top: 15px; font-size: 12px; color: #555; letter-spacing: 4px; }
.played-cards-stack { display: flex; gap: 10px; }
.table-card { transform: scale(0.85); }

/* 底部区域 */
.footer-zone {
  height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(to top, rgba(0,0,0,0.95), transparent);
}
.action-dock { height: 60px; display: flex; gap: 20px; align-items: center; }
.btn-play { background: #c0392b; color: #fff; border: none; padding: 12px 48px; border-radius: 24px; font-size: 1.2em; font-weight: bold; cursor: pointer; box-shadow: 0 4px 0 #922b21; }
.btn-play:disabled { background: #444; box-shadow: none; color: #777; cursor: not-allowed; transform: translateY(2px); }
.btn-end { background: #34495e; color: #fff; border: none; padding: 10px 24px; border-radius: 24px; cursor: pointer; }

.player-bottom-layout {
  width: 95%;
  max-width: 1400px;
  display: flex;
  align-items: flex-end;
  padding-bottom: 20px;
}
.my-avatar-box { width: 100px; flex-shrink: 0; }
.avatar-spacer { width: 100px; flex-shrink: 0; } /* 🌟 核心：右侧占位，确保手牌物理居中 */

.hand-cards-box {
  flex: 1;
  display: flex;
  justify-content: center;
  overflow: visible;
}
.hand-row {
  display: flex;
  justify-content: center;
  padding-left: 50px; /* 🌟 核心：补偿手牌负边距产生的向左偏移 */
}
.hand-row .card {
  margin-left: -50px;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform-origin: bottom center;
}
.hand-row .card:first-child { margin-left: 0; }
.hand-row .card:hover { transform: translateY(-30px) scale(1.1); z-index: 100; }
.hand-row .card.selected { transform: translateY(-60px) scale(1.05); z-index: 99; border-color: #f1c40f; box-shadow: 0 0 20px rgba(241, 196, 15, 0.5); }

/* 动画定义 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.list-enter-active { transition: all 0.5s ease; }
.list-enter-from { opacity: 0; transform: translateY(30px) scale(0.8); }
.hand-enter-active { transition: all 0.4s ease; }
.hand-enter-from { opacity: 0; transform: translateY(100px) rotate(10deg); }
</style>