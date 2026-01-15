<script setup>
import { computed } from 'vue';

// 接收父组件传来的卡牌数据
const props = defineProps({
  card: {
    type: Object,
    required: true
  }
});

// 字典：花色对应符号和颜色（改为更古风的配色）
const suitMap = {
  spade: { symbol: '♠', color: '#2c3e50' }, // 墨色
  heart: { symbol: '♥', color: '#c0392b' }, // 朱砂
  club: { symbol: '♣', color: '#2c3e50' },  // 墨色
  diamond: { symbol: '♦', color: '#c0392b' }, // 朱砂
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
const isEquip = computed(() => props.card.type && props.card.type.startsWith('equip')); // 装备牌
const isScroll = computed(() => props.card.type === 'scroll' || props.card.type === 'delayed'); // 锦囊牌

// 类型名称映射
const typeName = computed(() => {
  if (props.card.type === 'basic') return '基本';
  if (isEquip.value) return '装备';
  return '锦囊';
});
</script>

<template>
  <div class="card-frame" :class="{ 'type-equip': isEquip, 'type-scroll': isScroll, 'is-sha': isSha }">
    
    <div class="card-paper">
      
      <div class="card-header" :style="{ color: suitInfo.color }">
        <div class="rank">{{ rankText }}</div>
        <div class="suit">{{ suitInfo.symbol }}</div>
      </div>

      <div class="card-body">
        <span class="name">{{ card.name }}</span>
      </div>

      <div class="card-seal">
        {{ typeName }}
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
  width: 105px;  /* 略微加宽以适应边框 */
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
}

/* 悬停特效 */
.card-frame:hover {
  transform: translateY(-20px) scale(1.05);
  box-shadow: 0 10px 25px rgba(0,0,0,0.6);
  z-index: 50; /* 确保浮起时遮盖其他牌 */
}

/* 不同类型的边框颜色 */
.type-equip { background: linear-gradient(135deg, #1e5631, #27ae60); } /* 装备-翠绿 */
.type-scroll { background: linear-gradient(135deg, #154360, #2980b9); } /* 锦囊-深蓝 */

/* === 纸面纹理 === */
.card-paper {
  flex: 1;
  border-radius: 4px;
  background-color: var(--sgs-paper, #fdfbf7); /* 使用全局变量定义的宣纸色 */
  /* SVG 噪点纹理，模拟纸张杂质 */
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23d6d3c7' fill-opacity='0.4'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7z' /%3E%3C/g%3E%3C/svg%3E");
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* === 左上角信息 === */
.card-header {
  padding: 4px 6px;
  text-align: left;
  line-height: 0.9;
  font-family: serif;
}
.rank { font-size: 1.4em; font-weight: bold; }
.suit { font-size: 1.4em; margin-top: -2px; }

/* === 中央名称 (核心视觉) === */
.card-body {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-bottom: 10px;
}
.name {
  font-family: 'LiSu', 'STKaiti', serif; /* 隶书 */
  font-size: 28px;
  font-weight: bold;
  color: #1a1a1a;
  writing-mode: vertical-rl; /* 竖排文字 */
  letter-spacing: 4px;
  text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
  white-space: nowrap;
}

/* “杀”字的特殊样式 */
.is-sha .name {
  color: var(--sgs-red, #c0392b);
  font-family: 'KaiTi', serif; /* 楷体/行楷 */
  font-size: 46px; /* 更大 */
  text-shadow: 2px 2px 0 rgba(0,0,0,0.15);
}
.is-sha {
  border-color: #581b1b;
}

/* === 底部印章 === */
.card-seal {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-family: 'SgsFont', serif;
  color: #8d6e63;
  border: 1px solid #8d6e63;
  padding: 1px 4px;
  border-radius: 4px;
  opacity: 0.8;
  white-space: nowrap;
}

/* === 右上角角标 (范围/距离) === */
.range-badge {
  position: absolute;
  top: 4px; right: 4px;
  width: 18px; height: 18px;
  background: #212121;
  color: #fff;
  border-radius: 50%;
  font-size: 10px;
  display: flex; justify-content: center; align-items: center;
  border: 1px solid #aaa;
  box-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}
.range-badge span {
  font-size: 8px;
  transform: scale(0.7);
  margin-right: -1px;
  opacity: 0.8;
}

.range-badge.distance {
  top: 26px; /* 如果有两个角标，向下错开 */
  background: #2980b9;
}
</style>