<script setup>
import { computed } from 'vue';

// 接收父组件传来的状态
const props = defineProps({
  player: Object,      // 包含 sid, seat_id, hp, card_count, equips, avatar, nickname, username, kingdom 等
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

// 头像路径处理
const avatarUrl = computed(() => {
  if (!props.player) return ''; // 🛡️ 防御性检查
  const filename = props.player.avatar || 'default.png';
  if (filename === 'default.png') return 'https://api.dicebear.com/7.x/adventurer/svg?seed=' + props.player.sid;
  return `/avatars/${filename}`;
});

// 动态获取边框颜色
const borderColor = computed(() => {
  if (props.isSelected) return '#e74c3c'; // 红色选中
  if (props.isCurrent) return '#2ecc71';  // 绿色回合中
  if (props.isMe) return '#3498db';       // 蓝色自己
  return '#444';                          // 默认灰色
});

// 阵营样式映射
const kingdomStyle = computed(() => {
  if (!props.player) return { bg: '#000', text: '?', border: '#333' }; // 🛡️ 防御性检查
  const k = props.player.kingdom || 'god';
  const map = {
    wei: { bg: '#2980b9', text: '魏', border: '#2c3e50' }, // 魏-蓝
    shu: { bg: '#c0392b', text: '蜀', border: '#7f2f2f' }, // 蜀-红
    wu:  { bg: '#27ae60', text: '吴', border: '#1e5430' }, // 吴-绿
    qun: { bg: '#95a5a6', text: '群', border: '#555' },    // 群-灰
    god: { bg: '#000', text: '?', border: '#333' }
  };
  return map[k] || map.god;
});
</script>

<template>
  <div class="player-avatar-wrapper" v-if="player">
    <div 
      class="avatar-card" 
      :style="{ borderColor: borderColor }"
      :class="{ 'card-active': isCurrent, 'card-selected': isSelected, 'card-dead': !player.is_alive }"
    >
      <img :src="avatarUrl" class="avatar-img" alt="avatar" />
      
      <div class="kingdom-badge" :style="{ backgroundColor: kingdomStyle.bg, borderBottomColor: kingdomStyle.border }">
        {{ kingdomStyle.text }}
      </div>

      <div class="card-overlay"></div>

      <div class="seat-badge">{{ player.seat_id }}号</div>

      <div class="identity-name" :title="`账号: @${player.username || '未知'}`">
        {{ player.nickname || (isMe ? '我自己' : '无名氏') }}
      </div>
      
      <div class="stats-panel">
        <div class="stat-item hp" :class="{ 'low-hp': player.hp <= 1 }">
          <span class="icon">❤️</span> {{ Math.max(0, player.hp) }}
        </div>
        <div class="stat-item hand">
          <span class="icon">🎴</span> {{ player.card_count }}
        </div>
      </div>
      
      <div v-if="!player.is_alive" class="dead-mask">
        <span>阵亡</span>
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
  user-select: none;
}

/* === 头像卡片核心 === */
.avatar-card {
  width: 80px;
  height: 105px;
  background: #2c3e50;
  border: 3px solid #444;
  border-radius: 8px;
  position: relative;
  overflow: hidden; /* 裁剪图片圆角 */
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-shadow: 0 4px 6px rgba(0,0,0,0.4);
}

.avatar-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 12px rgba(0,0,0,0.6);
}

/* 选中与回合状态动画 */
.card-active {
  box-shadow: 0 0 15px rgba(46, 204, 113, 0.7) !important;
  border-color: #2ecc71 !important;
}
.card-selected {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(231, 76, 60, 0.8) !important;
  border-color: #e74c3c !important;
}

/* 死亡样式 */
.card-dead {
  filter: grayscale(1); /* 黑白滤镜 */
  opacity: 0.8;
  border-color: #2c3e50 !important;
  box-shadow: none !important;
  transform: none !important;
  cursor: default;
}

.dead-mask {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
}

.dead-mask span {
  color: #c0392b;
  font-size: 24px;
  font-weight: bold;
  font-family: "KaiTi", serif;
  border: 3px solid #c0392b;
  padding: 2px 8px;
  border-radius: 4px;
  transform: rotate(-15deg);
  text-shadow: 0 2px 4px #000;
  letter-spacing: 2px;
}

/* === 内部元素 === */
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0; left: 0;
  z-index: 1;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.2) 40%, transparent 100%);
  z-index: 2;
}

/* 阵营角标 */
.kingdom-badge {
  position: absolute;
  top: 0;
  right: 0;
  width: 22px;
  height: 22px;
  color: #fff;
  font-size: 13px;
  font-weight: bold;
  display: flex;
  justify-content: center;
  align-items: center;
  border-bottom-left-radius: 6px;
  z-index: 5;
  box-shadow: -1px 1px 3px rgba(0,0,0,0.5);
  font-family: "KaiTi", serif;
  text-shadow: 0 1px 1px rgba(0,0,0,0.5);
}

.seat-badge {
  position: absolute;
  top: 0;
  left: 0;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-bottom-right-radius: 6px;
  z-index: 3;
  border-right: 1px solid rgba(255,255,255,0.2);
  border-bottom: 1px solid rgba(255,255,255,0.2);
}

.identity-name {
  position: absolute;
  bottom: 24px; /* 在状态栏上方 */
  width: 100%;
  text-align: center;
  color: #fff;
  font-size: 12px;
  font-weight: bold;
  text-shadow: 0 1px 2px #000;
  z-index: 3;
  padding: 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* === 底部状态条 === */
.stats-panel {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 22px;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: space-evenly;
  z-index: 3;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.stat-item {
  font-size: 12px;
  color: #fff;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 2px;
}

.low-hp { color: #e74c3c; animation: blink 1s infinite; }

@keyframes blink { 50% { opacity: 0.5; } }

/* === 装备栏 === */
.equip-sidebar {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-top: 2px;
}

.equip-slot {
  width: 42px;
  height: 22px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 3px;
  display: flex;
  align-items: center;
  overflow: hidden;
  opacity: 0.5; /* 空装备半透明 */
}

.equip-slot.has-item {
  border-color: #f39c12;
  background: linear-gradient(90deg, #2c2500, #1a1a1a);
  opacity: 1;
}

.slot-type {
  font-size: 10px;
  color: #777;
  background: #000;
  width: 16px;
  text-align: center;
  height: 100%;
  line-height: 20px;
  flex-shrink: 0;
}

.has-item .slot-type { color: #f39c12; font-weight: bold; }

.equip-name {
  font-size: 10px;
  color: #f1c40f;
  padding-left: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}
</style>