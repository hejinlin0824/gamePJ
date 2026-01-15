<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { socket } from '@/services/socket';

const emit = defineEmits(['join']);

const rooms = ref([]);

// 刷新房间列表
const refreshLobby = () => {
  if (socket.connected) {
    socket.emit('get_lobby', {});
  }
};

onMounted(() => {
  refreshLobby();
  
  socket.on('lobby_update', (data) => {
    rooms.value = data;
  });

  socket.on('connect', refreshLobby);
});

onUnmounted(() => {
  socket.off('lobby_update');
  socket.off('connect', refreshLobby);
});

const handleDoubleClick = (roomId) => {
  emit('join', roomId);
};

// 状态文本映射
const getStatusText = (room) => {
  if (room.status === 'playing') return '⚔️ 两军交锋';
  if (room.status === 'waiting') return `🥁 招兵买马 ${room.count}/${room.max_count}`;
  return '🍃 空置营地';
};
</script>

<template>
  <div class="lobby-container">
    
    <div class="lobby-header">
      <button class="btn-refresh" @click="refreshLobby">
        <span>↻ 重探军情</span>
      </button>

      <div class="header-decoration left"></div>
      <h2 class="lobby-title">🔥 烽 火 演 武 台 🔥</h2>
      <div class="header-decoration right"></div>
    </div>

    <div class="room-grid">
      <div 
        v-for="room in rooms" 
        :key="room.room_id"
        class="room-card"
        :class="room.status"
        @dblclick="handleDoubleClick(room.room_id)"
      >
        <div class="room-badge">
          <span class="badge-text">{{ room.room_id }} 营</span>
        </div>
        
        <div class="status-icon">
          <span v-if="room.status === 'playing'" class="icon-clash">⚔️</span>
          <span v-else-if="room.status === 'waiting'" class="icon-tent">⛺</span>
          <span v-else class="icon-empty">🏳️</span>
        </div>

        <div class="room-info">
          <div class="status-text">{{ getStatusText(room) }}</div>
        </div>

        <div class="card-texture"></div>
        
        <div class="hint-text">双击入营</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 容器 */
.lobby-container {
  width: 100%; height: 100%;
  padding: 30px;
  /* 🌟 修改：增加顶部 padding，让标题整体下移一点，避免显得太拥挤 */
  padding-top: 50px; 
  box-sizing: border-box;
  display: flex; flex-direction: column;
  background: transparent;
}

/* === 顶部匾额 === */
.lobby-header {
  display: flex; justify-content: center; align-items: center;
  margin-bottom: 40px;
  position: relative;
  height: 60px;
  background: linear-gradient(to right, transparent, rgba(0,0,0,0.8), transparent);
  border-top: 2px solid var(--sgs-wood-light);
  border-bottom: 2px solid var(--sgs-wood-light);
}

.lobby-title {
  color: var(--sgs-gold);
  margin: 0 40px;
  text-shadow: 0 0 10px #e67e22, 0 2px 5px #000;
  font-family: 'LiSu', serif;
  font-size: 36px;
  letter-spacing: 8px;
  white-space: nowrap; /* 防止标题换行 */
}

/* 🌟 修改：按钮位置改为 left */
.btn-refresh {
  position: absolute; 
  left: 40px; /* 放在左侧，与右侧的用户栏形成对称 */
  background: var(--sgs-wood-dark);
  color: #d7ccc8;
  border: 1px solid var(--sgs-wood-light);
  padding: 8px 16px;
  border-radius: 4px;
  font-family: 'LiSu', serif;
  transition: all 0.2s;
  box-shadow: 0 4px 8px rgba(0,0,0,0.5);
  display: flex; align-items: center; gap: 5px;
}
.btn-refresh:hover {
  border-color: var(--sgs-gold);
  color: var(--sgs-gold);
  transform: scale(1.05);
}

/* === 房间网格 === */
.room-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 25px;
  overflow-y: auto;
  padding: 10px;
  /* 美化滚动条区域 */
  mask-image: linear-gradient(to bottom, transparent, black 10px, black 95%, transparent);
}

/* === 房间卡片 (令牌/木牌风格) === */
.room-card {
  height: 160px;
  background-color: #3e2723;
  background-image: repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 10px);
  border: 2px solid #5d4037;
  border-radius: 8px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex; flex-direction: column;
  align-items: center;
  user-select: none;
  box-shadow: 0 5px 15px rgba(0,0,0,0.6);
  overflow: hidden;
}

.room-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.8);
  border-color: var(--sgs-gold);
}
.room-card:hover .room-badge {
  background: var(--sgs-gold);
  color: #3e2723;
}

/* === 状态差异化 === */
.room-card.playing { border-color: #c0392b; box-shadow: 0 0 15px rgba(192, 57, 43, 0.3); }
.room-card.playing .status-text { color: #e74c3c; font-weight: bold; }
.room-card.playing .icon-clash { animation: clash 1s infinite alternate; display: inline-block; }

.room-card.waiting { border-color: #27ae60; }
.room-card.waiting .status-text { color: #2ecc71; }

.room-card.idle { opacity: 0.7; filter: grayscale(0.8); }

/* === 内部元素 === */
.room-badge {
  width: 100%;
  background: #212121;
  color: #aaa;
  padding: 5px 0;
  text-align: center;
  font-family: 'LiSu', serif;
  font-size: 18px;
  border-bottom: 1px solid #5d4037;
  transition: all 0.2s;
}

.status-icon {
  flex: 1;
  display: flex; justify-content: center; align-items: center;
  font-size: 48px; opacity: 0.8;
  text-shadow: 0 5px 10px rgba(0,0,0,0.5);
}

.room-info { margin-bottom: 25px; text-align: center; }
.status-text { font-size: 16px; font-family: 'LiSu', serif; text-shadow: 0 2px 2px #000; }

.hint-text {
  position: absolute; bottom: 5px;
  font-size: 12px; color: #888;
  opacity: 0; transition: opacity 0.2s;
}
.room-card:hover .hint-text { opacity: 1; }

/* 装饰铆钉 */
.room-card::after, .room-card::before {
  content: ''; position: absolute; width: 6px; height: 6px;
  background: #111; border-radius: 50%; box-shadow: 0 1px 0 rgba(255,255,255,0.2);
}
.room-card::before { top: 6px; left: 6px; box-shadow: 180px 0 0 0 #111, 0 1px 0 rgba(255,255,255,0.2); }
.room-card::after { bottom: 6px; left: 6px; box-shadow: 180px 0 0 0 #111, 0 1px 0 rgba(255,255,255,0.2); }

@keyframes clash {
  from { transform: scale(1); filter: drop-shadow(0 0 0 rgba(231,76,60,0)); }
  to { transform: scale(1.1); filter: drop-shadow(0 0 10px rgba(231,76,60,0.8)); }
}
</style>