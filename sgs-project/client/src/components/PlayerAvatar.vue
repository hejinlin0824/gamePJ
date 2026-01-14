<script setup>
// 接收父组件传来的状态
const props = defineProps({
  player: Object,      // 包含 sid, seat_id, hp, card_count, equips 等
  isCurrent: Boolean,  // 是否是当前回合
  isSelected: Boolean, // 是否被我选中为目标
  isMe: Boolean        // 是否是玩家自己
});

// 装备槽位名称映射
const slotLabels = {
  weapon: "武",
  armor: "防",
  horse_plus: "让",
  horse_minus: "追"
};
</script>

<template>
  <div class="player-avatar-wrapper">
    <div 
      class="avatar-card" 
      :class="{ 
        'turn-active': isCurrent, 
        'target-selected': isSelected,
        'me-border': isMe 
      }"
    >
      <div class="seat-index">{{ player.seat_id }}号</div>
      <div class="role-name">{{ isMe ? '我' : '对手' }}</div>
      
      <div class="stats-panel">
        <div class="stat-item hp">❤️ {{ player.hp }}</div>
        <div class="stat-item hand">🎴 {{ player.card_count }}</div>
      </div>
    </div>

    <div class="equip-sidebar">
      <div 
        v-for="(name, slot) in player.equips" 
        :key="slot" 
        class="equip-slot" 
        :class="{ 'has-item': name }"
        :title="name || '空'"
      >
        <span class="slot-type">{{ slotLabels[slot] }}</span>
        <span class="equip-name">{{ name || '' }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.player-avatar-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  position: relative;
}

/* 头像卡片样式 */
.avatar-card {
  width: 75px;
  height: 95px;
  background: #2c3e50;
  border: 2px solid #444;
  border-radius: 6px;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  cursor: pointer;
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.avatar-card:hover { border-color: #999; }

/* 状态高亮 */
.turn-active {
  border-color: #2ecc71 !important;
  box-shadow: 0 0 15px rgba(46, 204, 113, 0.6) !important;
}
.target-selected {
  border-color: #e74c3c !important;
  transform: scale(1.05);
  background: #411 !important;
}
.me-border { border-color: #3498db; }

.seat-index {
  position: absolute;
  top: -8px;
  left: -8px;
  background: #333;
  color: #fff;
  font-size: 10px;
  padding: 2px 5px;
  border-radius: 4px;
  border: 1px solid #666;
}

.role-name {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #ecf0f1;
  font-size: 1.2em;
}

.stats-panel {
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: space-around;
  padding: 2px 0;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
}

.stat-item { font-size: 11px; color: #fff; }

/* === 装备栏样式 === */
.equip-sidebar {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.equip-slot {
  width: 42px;
  height: 21px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 2px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.equip-slot.has-item {
  border-color: #f1c40f;
  background: #2c2500;
}

.slot-type {
  font-size: 9px;
  color: #777;
  background: #000;
  width: 14px;
  text-align: center;
  height: 100%;
  line-height: 20px;
}

.has-item .slot-type { color: #f1c40f; }

.equip-name {
  font-size: 9px;
  color: #f1c40f;
  padding-left: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}
</style>