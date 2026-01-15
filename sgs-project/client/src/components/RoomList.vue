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
  // 1. 挂载时刷新
  refreshLobby();
  
  // 2. 监听服务器推送到的大厅更新
  socket.on('lobby_update', (data) => {
    rooms.value = data;
  });

  // 3. 监听重连事件：断线重连后自动刷新大厅
  socket.on('connect', refreshLobby);
});

onUnmounted(() => {
  socket.off('lobby_update');
  socket.off('connect', refreshLobby);
});

const handleDoubleClick = (roomId) => {
  emit('join', roomId);
};

// 状态颜色映射
const getStatusColor = (status) => {
  if (status === 'playing') return '#c0392b'; // 激战红
  if (status === 'waiting') return '#27ae60'; // 等待绿
  return '#7f8c8d'; // 空闲灰
};

const getStatusText = (room) => {
  if (room.status === 'playing') return '⚔️ 激战中';
  if (room.status === 'waiting') return `👥 等待中 (${room.count}/${room.max_count})`;
  return '🍃 虚位以待';
};
</script>

<template>
  <div class="lobby-container">
    <div class="lobby-header">
      <h2 class="lobby-title">🔥 烽火台 · 演武场 🔥</h2>
      <button class="btn-refresh" @click="refreshLobby">↻ 刷新军情</button>
    </div>

    <div class="room-grid">
      <div 
        v-for="room in rooms" 
        :key="room.room_id"
        class="room-card"
        :class="room.status"
        @dblclick="handleDoubleClick(room.room_id)"
      >
        <div class="room-id-badge">{{ room.room_id }}号营</div>
        
        <div class="room-status" :style="{ color: getStatusColor(room.status) }">
          {{ getStatusText(room) }}
        </div>

        <div class="room-decoration">
          <span v-if="room.status === 'playing'">🔥</span>
          <span v-else-if="room.status === 'waiting'">⛺</span>
          <span v-else>🏳️</span>
        </div>
        
        <div class="hint-text">双击加入</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lobby-container {
  width: 100%; height: 100%;
  padding: 20px;
  box-sizing: border-box;
  display: flex; flex-direction: column;
}

.lobby-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
  background: rgba(0,0,0,0.6);
  padding: 10px 20px;
  border-radius: 8px;
  border-bottom: 2px solid #d4af37;
}

.lobby-title {
  color: #f1c40f;
  margin: 0;
  text-shadow: 0 2px 4px #000;
  font-family: "KaiTi", "STKaiti", serif;
  font-size: 28px;
  letter-spacing: 2px;
}

.btn-refresh {
  background: #34495e; color: #fff; border: 1px solid #7f8c8d;
  padding: 8px 16px; cursor: pointer; border-radius: 4px;
  font-family: inherit;
  transition: all 0.2s;
}
.btn-refresh:hover { background: #2c3e50; border-color: #fff; transform: scale(1.05); }

.room-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
  overflow-y: auto;
  padding-bottom: 20px;
}

/* 滚动条美化 */
.room-grid::-webkit-scrollbar { width: 8px; }
.room-grid::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
.room-grid::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }

.room-card {
  height: 140px;
  background: rgba(44, 62, 80, 0.9);
  border: 2px solid #555;
  border-radius: 8px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  user-select: none;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.room-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.6);
  border-color: #f1c40f;
  z-index: 10;
}

/* 状态样式差异化 */
.room-card.playing { border-color: #c0392b; background: linear-gradient(135deg, rgba(60, 20, 20, 0.95), rgba(44, 62, 80, 0.9)); }
.room-card.waiting { border-color: #27ae60; background: linear-gradient(135deg, rgba(20, 60, 30, 0.95), rgba(44, 62, 80, 0.9)); }

.room-id-badge {
  position: absolute; top: 0; left: 0;
  background: rgba(0,0,0,0.8); color: #fff;
  padding: 4px 8px; border-bottom-right-radius: 8px;
  font-size: 12px; font-weight: bold;
}

.room-status {
  font-size: 16px; font-weight: bold;
  margin-bottom: 5px;
  text-shadow: 0 1px 2px #000;
}

.room-decoration { font-size: 40px; opacity: 0.5; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); }

.hint-text {
  font-size: 10px; color: #aaa;
  position: absolute; bottom: 5px;
  opacity: 0.7;
}
</style>