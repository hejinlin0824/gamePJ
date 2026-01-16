<script setup>
import { computed } from 'vue';

// 接收父组件传来的卡牌数据
const props = defineProps({
  card: {
    type: Object,
    required: true
  }
});

// 字典：花色对应符号和颜色
const suitMap = {
  spade: { symbol: '♠', color: '#2c3e50' }, // 黑桃-墨黑
  club: { symbol: '♣', color: '#2c3e50' },  // 梅花-墨黑
  heart: { symbol: '♥', color: '#c0392b' }, // 红桃-朱砂红
  diamond: { symbol: '♦', color: '#c0392b' }, // 方块-朱砂红
  none: { symbol: '', color: 'gray' }
};

// 字典：点数对应文本
const rankMap = {
  1: 'A', 11: 'J', 12: 'Q', 13: 'K'
};

// 计算属性
const suitInfo = computed(() => suitMap[props.card.suit] || suitMap.none);
const rankText = computed(() => rankMap[props.card.rank] || props.card.rank);

// 类型判断
const isSha = computed(() => props.card.name === '杀');
const isEquip = computed(() => props.card.type && props.card.type.startsWith('equip')); 
const isScroll = computed(() => props.card.type === 'scroll' || props.card.type === 'delayed');
const isDelayed = computed(() => props.card.type === 'delayed');

// 类型名称映射
const typeName = computed(() => {
  if (props.card.type === 'basic') return '基本';
  if (isEquip.value) return '装备';
  if (isDelayed.value) return '延时';
  if (isScroll.value) return '锦囊';
  return '牌';
});
</script>

<template>
  <div class="card-frame" :class="{ 'type-equip': isEquip, 'type-scroll': isScroll, 'is-sha': isSha }">
    
    <div class="card-paper">
      
      <div class="card-header-left" :style="{ color: suitInfo.color }">
        <div class="rank">{{ rankText }}</div>
        <div class="suit">{{ suitInfo.symbol }}</div>
      </div>

      <div class="card-header-right" :style="{ color: suitInfo.color }">
        <div class="rank-small">{{ rankText }}</div>
      </div>

      <div class="card-body">
        <span class="name">{{ card.name }}</span>
      </div>

      <div class="card-footer">
        <div class="card-seal">{{ typeName }}</div>
      </div>
      
      <div v-if="card.attack_range" class="range-badge">
        <span>攻</span>{{ card.attack_range }}
      </div>
      
      <div v-if="card.distance_limit" class="range-badge distance">
        <span>距</span>{{ card.distance_limit }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* === 卡牌整体容器 === */
.card-frame {
  width: 105px;  
  height: 150px;
  border-radius: 6px;
  padding: 4px; /* 内边距形成外框 */
  background: #3e2723; /* 默认深棕外框 */
  box-shadow: 2px 4px 8px rgba(0,0,0,0.4);
  display: flex;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  user-select: none;
  /* 🌟 关键：防止文字溢出 */
  overflow: hidden;
}

/* 悬停特效 */
.card-frame:hover {
  /* 这里的 hover 主要用于桌面牌堆，手牌的 hover 由 App.vue 控制 */
  box-shadow: 0 10px 25px rgba(0,0,0,0.6);
}

/* 不同类型的边框颜色 */
.type-equip { background: linear-gradient(135deg, #145a32, #27ae60); } /* 装备-翠绿 */
.type-scroll { background: linear-gradient(135deg, #154360, #2980b9); } /* 锦囊-深蓝 */

/* === 纸面纹理 === */
.card-paper {
  flex: 1;
  border-radius: 4px;
  background-color: #fdfbf7; /* 宣纸色 */
  /* SVG 噪点纹理 */
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23d6d3c7' fill-opacity='0.4'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7z' /%3E%3C/g%3E%3C/svg%3E");
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* === 角标信息 === */
.card-header-left {
  position: absolute;
  top: 2px; left: 4px;
  text-align: center;
  line-height: 0.9;
  font-family: serif;
}
.rank { font-size: 1.4em; font-weight: bold; display: block; }
.suit { font-size: 1.2em; margin-top: -2px; display: block; }

/* 🌟 右上角小角标 (专为堆叠设计) */
.card-header-right {
  position: absolute;
  top: 4px; right: 4px;
  opacity: 0.6;
}
.rank-small { font-size: 10px; font-weight: bold; font-family: serif; }

/* === 中央名称 (核心视觉) === */
.card-body {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-left: 10px; /* 给左侧角标留点空隙，防止文字重叠 */
}
.name {
  font-family: 'LiSu', 'STKaiti', serif; /* 隶书 */
  font-size: 26px;
  font-weight: bold;
  color: #1a1a1a;
  writing-mode: vertical-rl; /* 竖排文字 */
  letter-spacing: 4px;
  text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
  white-space: nowrap;
}

/* “杀”字的特殊样式 */
.is-sha .name {
  color: #c0392b; /* 杀气红 */
  font-family: 'KaiTi', serif;
  font-size: 42px; /* 更大 */
  text-shadow: 2px 2px 0 rgba(0,0,0,0.15);
}
.is-sha {
  border-color: #581b1b;
}

/* === 底部印章 === */
.card-footer {
  position: absolute;
  bottom: 4px; width: 100%;
  display: flex; justify-content: center;
}
.card-seal {
  font-size: 10px;
  font-family: 'SgsFont', serif;
  color: #8d6e63;
  border: 1px solid #8d6e63;
  padding: 0 4px;
  border-radius: 3px;
  opacity: 0.8;
  background: rgba(255,255,255,0.5);
}

/* === 右上角功能角标 (范围/距离) === */
/* 注意：为了避开右上角的点数，我们需要调整这个位置，改到右下或者左下 */
.range-badge {
  position: absolute;
  bottom: 22px; right: 4px; /* 改到底部 */
  width: 16px; height: 16px;
  background: #212121;
  color: #fff;
  border-radius: 50%;
  font-size: 9px;
  display: flex; justify-content: center; align-items: center;
  border: 1px solid #aaa;
  box-shadow: 1px 1px 2px rgba(0,0,0,0.3);
  z-index: 2;
}
.range-badge span {
  font-size: 7px;
  transform: scale(0.8);
  margin-right: -1px;
  opacity: 0.8;
}

.range-badge.distance {
  bottom: 4px; right: 4px; /* 再往下一点 */
  background: #2980b9;
}
</style>