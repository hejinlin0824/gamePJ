<script setup>
import { computed } from 'vue';

// 接收父组件传来的状态
const props = defineProps({
  player: Object,      // 包含 sid, seat_id, hp, max_hp, card_count, equips, avatar, nickname, kingdom 等
  isCurrent: Boolean,  // 是否是当前回合
  isSelected: Boolean, // 是否被我选中为目标
  isMe: Boolean        // 是否是玩家自己
});

// 装备槽位名称映射
const slotLabels = {
  weapon: "武",
  armor: "防",
  horse_plus: "+1",
  horse_minus: "-1"
};

// 头像路径处理
const avatarUrl = computed(() => {
  if (!props.player) return '';
  const filename = props.player.avatar || 'default.png';
  if (filename === 'default.png') return 'https://api.dicebear.com/7.x/adventurer/svg?seed=' + props.player.sid;
  return `/avatars/${filename}`;
});

// 阵营样式映射
const kingdomClass = computed(() => props.player?.kingdom || 'god');

// 边框光效
const borderClass = computed(() => {
  if (props.isSelected) return 'border-selected';
  if (props.isCurrent) return 'border-active';
  return '';
});
</script>

<template>
  <div class="player-wrapper" v-if="player">
    
    <div class="general-card" :class="[kingdomClass, borderClass, { 'is-dead': !player.is_alive }]">
      
      <div class="kingdom-seal">
        {{ player.kingdom === 'god' ? '神' : player.kingdom.toUpperCase() }}
      </div>

      <div v-if="player.is_host" class="host-flag">主</div>

      <div class="avatar-box">
        <img :src="avatarUrl" class="avatar-img" />
        <div v-if="!player.is_alive" class="death-stamp">
          <span>阵亡</span>
        </div>
      </div>

      <div class="info-bar">
        <span class="seat-badge">{{ player.seat_id }}</span>
        <span class="nickname">{{ player.nickname }}</span>
      </div>

      <div class="status-bar">
        <div class="hp-rack">
          <span 
            v-for="i in player.max_hp" 
            :key="i" 
            class="magatama"
            :class="{ 'lost': i > player.hp }"
          >
            ☯
          </span>
        </div>
        <div class="hand-counter">
          <span class="icon">🎴</span>{{ player.card_count }}
        </div>
      </div>
    </div>

    <div class="equip-sidebar">
      <div 
        v-for="(cardName, slot) in player.equips" 
        :key="slot" 
        class="equip-slot"
        :class="{ 'has-item': cardName }"
        :title="cardName || '空'"
      >
        <div class="slot-label">{{ slotLabels[slot] }}</div>
        <div class="equip-name">{{ cardName ? cardName : '' }}</div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.player-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 2px;
  position: relative;
  transition: all 0.3s ease;
}

/* === 武将卡容器 === */
.general-card {
  width: 120px;
  height: 160px;
  background-color: #222;
  border: 2px solid #444; /* 默认边框 */
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0,0,0,0.5);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

/* 阵营主题色边框 */
.general-card.wei { border-color: #2980b9; }
.general-card.shu { border-color: #c0392b; }
.general-card.wu { border-color: #27ae60; }
.general-card.qun { border-color: #95a5a6; }

/* 状态光效 */
.border-active {
  box-shadow: 0 0 15px var(--sgs-gold, #f1c40f);
  border-color: var(--sgs-gold, #f1c40f) !important;
  z-index: 10;
}
.border-selected {
  box-shadow: 0 0 20px var(--sgs-red, #e74c3c);
  border-color: var(--sgs-red, #e74c3c) !important;
  transform: scale(1.05);
  z-index: 11;
}

/* 死亡状态 */
.is-dead {
  filter: grayscale(100%) brightness(50%);
  border-color: #333 !important;
  cursor: default;
}

/* === 内部元素 === */

/* 阵营印章 */
.kingdom-seal {
  position: absolute; top: 0; left: 0;
  width: 24px; height: 24px;
  background: rgba(0,0,0,0.8);
  color: #fff;
  font-family: 'LiSu', serif;
  font-size: 16px;
  display: flex; justify-content: center; align-items: center;
  border-bottom-right-radius: 6px;
  z-index: 5;
  border-right: 1px solid rgba(255,255,255,0.2);
  border-bottom: 1px solid rgba(255,255,255,0.2);
}
.wei .kingdom-seal { background: linear-gradient(135deg, #2980b9, #154360); }
.shu .kingdom-seal { background: linear-gradient(135deg, #c0392b, #641e16); }
.wu .kingdom-seal { background: linear-gradient(135deg, #27ae60, #145a32); }
.qun .kingdom-seal { background: linear-gradient(135deg, #95a5a6, #424949); }

/* 房主旗 */
.host-flag {
  position: absolute; top: 0; right: 0;
  background: var(--sgs-gold); color: #3e2723;
  font-size: 10px; font-weight: bold;
  padding: 1px 4px;
  border-bottom-left-radius: 4px;
  z-index: 5;
}

/* 头像 */
.avatar-box {
  width: 100%; height: 115px;
  background: #333;
  position: relative;
}
.avatar-img {
  width: 100%; height: 100%;
  object-fit: cover;
}
.death-stamp {
  position: absolute; inset: 0;
  display: flex; justify-content: center; align-items: center;
  background: rgba(0,0,0,0.4);
}
.death-stamp span {
  font-family: 'LiSu', serif;
  font-size: 28px;
  color: var(--sgs-red);
  border: 3px solid var(--sgs-red);
  padding: 2px 8px;
  border-radius: 4px;
  transform: rotate(-15deg);
  text-shadow: 0 2px 4px #000;
  letter-spacing: 2px;
}

/* 信息条 */
.info-bar {
  height: 20px;
  background: rgba(0,0,0,0.85);
  display: flex; align-items: center;
  padding: 0 4px;
  border-top: 1px solid #333;
  position: relative;
  z-index: 2;
}
.seat-badge {
  background: #555; color: #fff;
  font-size: 10px; width: 14px; height: 14px;
  border-radius: 50%;
  text-align: center; line-height: 14px;
  margin-right: 4px; flex-shrink: 0;
}
.nickname {
  font-size: 11px; color: #ecf0f1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* 状态栏 (底座) */
.status-bar {
  flex: 1;
  background: #1a1a1a;
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 0 6px;
  border-top: 1px solid #333;
}

/* 勾玉 */
.hp-rack {
  display: flex; gap: 1px; flex-wrap: wrap; max-width: 70%;
}
.magatama {
  font-size: 10px; line-height: 1;
  color: #2ecc71; /* 绿色勾玉 */
  text-shadow: 0 0 2px #000;
  transform: scale(1.2);
}
.magatama.lost {
  color: #555; /* 灰色空心 */
  opacity: 0.5;
}

/* 手牌数 */
.hand-counter {
  font-size: 12px; font-weight: bold;
  color: var(--sgs-gold);
}
.hand-counter .icon { font-size: 10px; margin-right: 1px; }

/* === 装备侧边栏 === */
.equip-sidebar {
  display: flex; flex-direction: column; gap: 2px;
  width: 18px;
  padding-top: 20px; /* 避开左上角印章 */
}

.equip-slot {
  width: 100%; height: 22px;
  background: #2c2c2c;
  border: 1px solid #3e2723;
  border-radius: 2px;
  display: flex; align-items: center;
  overflow: hidden;
  opacity: 0.6;
  font-size: 9px;
  color: #aaa;
}

.equip-slot.has-item {
  background: linear-gradient(90deg, #1b2631, #2c3e50);
  border-color: var(--sgs-gold);
  color: var(--sgs-gold);
  opacity: 1;
  box-shadow: 1px 1px 3px rgba(0,0,0,0.5);
}

.slot-label {
  width: 100%; text-align: center;
  font-weight: bold;
}

.has-item .slot-label { display: none; } /* 有装备时隐藏武/防字，或者显示首字 */
.has-item .equip-name {
  display: block; width: 100%;
  text-align: center;
  transform: scale(0.8);
  white-space: nowrap;
}
.equip-name { display: none; }
</style>