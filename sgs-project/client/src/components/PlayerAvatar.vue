<script setup>
// 接收父组件传来的属性
defineProps({
  player: Object,      // 玩家数据对象
  isCurrent: Boolean,  // 是否是当前回合
  isSelected: Boolean, // 是否被选中（作为攻击目标）
  isMe: Boolean        // 是否是自己
});
</script>

<template>
  <div 
    class="avatar" 
    :class="{ 
      'current-turn': isCurrent, 
      'selected': isSelected, 
      'is-me': isMe 
    }"
  >
    <div class="role-img">
      {{ player.seat_id }}号
    </div>
    
    <div class="info">
      <div class="hp-bar">❤️ {{ player.hp }}</div>
      <div class="cards-icon">🎴 {{ player.card_count }}</div>
    </div>
    
    <div v-if="isSelected" class="target-mark">🎯 目标</div>
    
    <div v-if="isMe" class="me-mark">我</div>
  </div>
</template>

<style scoped>
.avatar {
  width: 80px;
  height: 100px;
  background: #34495e; /* 深蓝灰色背景 */
  border: 2px solid #555;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.avatar:hover { 
  border-color: #aaa; 
  transform: translateY(-2px);
}

/* 当前回合玩家：绿色呼吸灯效果 */
.current-turn { 
  border-color: #2ecc71; 
  box-shadow: 0 0 15px rgba(46, 204, 113, 0.5); 
}

/* 被选中为目标：红色高亮 */
.selected { 
  border-color: #e74c3c; 
  background: #522; 
  transform: scale(1.1); 
  z-index: 10;
}

/* 自己：蓝色边框 */
.is-me {
  border-color: #3498db;
}

.role-img { 
  flex: 1; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-size: 1.5em; 
  font-weight: bold; 
  color: #fff; 
}

.info { 
  background: rgba(0,0,0,0.6); 
  padding: 4px; 
  font-size: 0.8em; 
  color: white;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
  display: flex;
  justify-content: space-between;
}

.target-mark {
  position: absolute; 
  top: -10px; 
  right: -10px;
  background: #c0392b; 
  color: white; 
  padding: 2px 6px; 
  border-radius: 4px; 
  font-size: 0.7em;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.me-mark {
  position: absolute;
  top: -10px;
  left: -10px;
  background: #2980b9;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7em;
}
</style>