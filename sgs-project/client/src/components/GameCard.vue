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
  spade: { symbol: '♠', color: 'black' },
  heart: { symbol: '♥', color: '#d63031' }, // 红色
  club: { symbol: '♣', color: 'black' },
  diamond: { symbol: '♦', color: '#d63031' }, // 红色
  none: { symbol: '', color: 'gray' }
};

// 字典：点数对应文本
const rankMap = {
  1: 'A', 11: 'J', 12: 'Q', 13: 'K'
};

// 计算属性
const suitInfo = computed(() => suitMap[props.card.suit] || suitMap.none);
const rankText = computed(() => rankMap[props.card.rank] || props.card.rank);
const isRed = computed(() => ['heart', 'diamond'].includes(props.card.suit));

// 简单判断是否是“杀”（用于特殊样式）
const isSha = computed(() => props.card.name === '杀');
</script>

<template>
  <div class="card" :class="{ 'is-sha': isSha }">
    <div class="card-header" :style="{ color: suitInfo.color }">
      <div class="rank">{{ rankText }}</div>
      <div class="suit">{{ suitInfo.symbol }}</div>
    </div>

    <div class="card-body">
      <span class="name">{{ card.name }}</span>
    </div>

    <div class="card-footer">
      <span class="type-tag">{{ card.type === 'basic' ? '基本' : '锦囊' }}</span>
    </div>
  </div>
</template>

<style scoped>
/* 卡牌容器 */
.card {
  width: 100px;  /* 标准扑克牌比例 */
  height: 140px;
  background: linear-gradient(135deg, #fffcf5 0%, #f1f2f6 100%);
  border-radius: 8px;
  border: 2px solid #7f8c8d;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  user-select: none;
}

/* 鼠标悬停特效 */
.card:hover {
  transform: translateY(-15px) scale(1.05);
  box-shadow: 0 10px 20px rgba(0,0,0,0.4);
  z-index: 10;
}

/* 左上角信息 */
.card-header {
  padding: 4px 8px;
  text-align: left;
  line-height: 1;
  font-family: serif;
}
.rank { font-size: 1.2em; font-weight: bold; }
.suit { font-size: 1.2em; }

/* 中央名称 */
.card-body {
  flex: 1; /* 撑满中间 */
  display: flex;
  justify-content: center;
  align-items: center;
}
.name {
  font-family: "KaiTi", "SimKai", serif; /* 楷体 */
  font-size: 2em;
  font-weight: bold;
  color: #2c3e50;
  text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
}

/* “杀”字的特殊样式 */
.is-sha .name {
  color: #c0392b; /* 深红 */
}
.is-sha {
  border-color: #581b1b;
}

/* 底部 */
.card-footer {
  font-size: 0.6em;
  color: #95a5a6;
  text-align: center;
  padding-bottom: 4px;
}
</style>