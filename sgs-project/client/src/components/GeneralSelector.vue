<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  candidates: {
    type: Array, // ['caocao', 'zhaoyun', 'guojia']
    required: true
  }
});

const emit = defineEmits(['select']);

// 简易前端数据字典，用于将 ID 转为中文显示
// 实际项目中，这些数据最好由后端 API 返回，或存储在单独的 json 文件中
const generalMap = {
  "caocao": { name: "曹操", kingdom: "wei", skill: "奸雄/护驾" },
  "guojia": { name: "郭嘉", kingdom: "wei", skill: "天妒/遗计" },
  "simayi": { name: "司马懿", kingdom: "wei", skill: "反馈/鬼才" },
  "xiahoudun": { name: "夏侯惇", kingdom: "wei", skill: "刚烈" },
  "zhangliao": { name: "张辽", kingdom: "wei", skill: "突袭" },
  "xuchu": { name: "许褚", kingdom: "wei", skill: "裸衣" },
  "zhenji": { name: "甄姬", kingdom: "wei", skill: "洛神/倾国" },
  
  "liubei": { name: "刘备", kingdom: "shu", skill: "仁德/激将" },
  "guanyu": { name: "关羽", kingdom: "shu", skill: "武圣" },
  "zhangfei": { name: "张飞", kingdom: "shu", skill: "咆哮" },
  "zhugeliang": { name: "诸葛亮", kingdom: "shu", skill: "观星/空城" },
  "zhaoyun": { name: "赵云", kingdom: "shu", skill: "龙胆" },
  "machao": { name: "马超", kingdom: "shu", skill: "马术/铁骑" },
  "huangyueying": { name: "黄月英", kingdom: "shu", skill: "集智/奇才" },
  
  "sunquan": { name: "孙权", kingdom: "wu", skill: "制衡/救援" },
  "ganning": { name: "甘宁", kingdom: "wu", skill: "奇袭" },
  "lvmeng": { name: "吕蒙", kingdom: "wu", skill: "克己" },
  "huanggai": { name: "黄盖", kingdom: "wu", skill: "苦肉" },
  "zhouyu": { name: "周瑜", kingdom: "wu", skill: "英姿/反间" },
  "daqiao": { name: "大乔", kingdom: "wu", skill: "国色/流离" },
  "luxun": { name: "陆逊", kingdom: "wu", skill: "谦逊/连营" },
  "sunshangxiang": { name: "孙尚香", kingdom: "wu", skill: "结姻/枭姬" },
  
  "huatuo": { name: "华佗", kingdom: "qun", skill: "青囊/急救" },
  "lvbu": { name: "吕布", kingdom: "qun", skill: "无双" },
  "diaochan": { name: "貂蝉", kingdom: "qun", skill: "离间/闭月" },
  "yuanshu": { name: "袁术", kingdom: "qun", skill: "庸肆/伪帝" },
  "huaxiong": { name: "华雄", kingdom: "qun", skill: "耀武/负勇" }
};

const selectedId = ref(null);

const handleSelect = (id) => {
  selectedId.value = id;
};

const confirmSelection = () => {
  if (selectedId.value) {
    emit('select', selectedId.value);
  }
};

const getInfo = (id) => generalMap[id] || { name: id, kingdom: "god", skill: "???" };

// 势力颜色映射
const kingdomColors = {
  wei: "linear-gradient(135deg, #2c3e50, #4a69bd)", // 魏-蓝
  shu: "linear-gradient(135deg, #c0392b, #e74c3c)", // 蜀-红
  wu: "linear-gradient(135deg, #27ae60, #2ecc71)",  // 吴-绿
  qun: "linear-gradient(135deg, #7f8c8d, #95a5a6)", // 群-灰
  god: "#000"
};
</script>

<template>
  <div class="selector-overlay">
    <div class="selector-modal">
      <h2 class="title">✨ 请择良将 ✨</h2>
      
      <div class="card-container">
        <div 
          v-for="id in candidates" 
          :key="id"
          class="general-card"
          :class="{ active: selectedId === id }"
          :style="{ background: kingdomColors[getInfo(id).kingdom] }"
          @click="handleSelect(id)"
        >
          <div class="kingdom-tag">{{ getInfo(id).kingdom.toUpperCase() }}</div>
          <div class="general-name">{{ getInfo(id).name }}</div>
          <div class="general-skills">{{ getInfo(id).skill }}</div>
          
          <div v-if="selectedId === id" class="check-mark">✔</div>
        </div>
      </div>

      <button 
        class="btn-confirm" 
        :disabled="!selectedId"
        @click="confirmSelection"
      >
        确认选择
      </button>
    </div>
  </div>
</template>

<style scoped>
.selector-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.85);
  backdrop-filter: blur(5px);
  z-index: 2000;
  display: flex; justify-content: center; align-items: center;
}

.selector-modal {
  background: #1a1a1a;
  padding: 40px;
  border-radius: 12px;
  border: 2px solid #d4af37;
  text-align: center;
  box-shadow: 0 0 30px rgba(212, 175, 55, 0.2);
}

.title {
  color: #f1c40f;
  margin-bottom: 30px;
  font-size: 2em;
  text-shadow: 0 2px 4px #000;
}

.card-container {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.general-card {
  width: 140px;
  height: 200px;
  border-radius: 8px;
  border: 3px solid #444;
  cursor: pointer;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  transition: all 0.2s;
  color: #fff;
  box-shadow: 0 5px 15px rgba(0,0,0,0.5);
  overflow: hidden;
}

.general-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.7);
}

.general-card.active {
  border-color: #f1c40f;
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(241, 196, 15, 0.6);
}

.kingdom-tag {
  position: absolute; top: 5px; left: 5px;
  font-size: 12px; font-weight: bold; opacity: 0.7;
}

.general-name {
  font-size: 24px;
  font-weight: bold;
  font-family: "KaiTi", serif;
  text-shadow: 0 2px 4px rgba(0,0,0,0.8);
  margin-bottom: 10px;
}

.general-skills {
  font-size: 12px;
  padding: 0 10px;
  opacity: 0.9;
}

.check-mark {
  position: absolute; top: 5px; right: 5px;
  background: #27ae60; color: #fff;
  width: 24px; height: 24px; border-radius: 50%;
  line-height: 24px; font-size: 14px;
}

.btn-confirm {
  background: linear-gradient(to bottom, #f1c40f, #b7892b);
  border: none;
  padding: 12px 40px;
  font-size: 18px;
  font-weight: bold;
  color: #2c1e15;
  border-radius: 30px;
  cursor: pointer;
  transition: filter 0.2s;
}

.btn-confirm:disabled {
  filter: grayscale(1);
  cursor: not-allowed;
  opacity: 0.5;
}

.btn-confirm:hover:not(:disabled) {
  filter: brightness(1.1);
}
</style>