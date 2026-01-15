<script setup>
import { ref } from 'vue';

const props = defineProps({
  candidates: {
    type: Array, // ['caocao', 'zhaoyun', 'guojia']
    required: true
  }
});

const emit = defineEmits(['select']);

// 前端数据字典：用于将 ID 转为中文显示及技能预览
// (注：实际项目中这些通常由后端传回，这里为了纯前端展示保留映射)
const generalMap = {
  "caocao": { name: "曹操", kingdom: "wei", skill: "奸雄 / 护驾" },
  "guojia": { name: "郭嘉", kingdom: "wei", skill: "天妒 / 遗计" },
  "simayi": { name: "司马懿", kingdom: "wei", skill: "反馈 / 鬼才" },
  "xiahoudun": { name: "夏侯惇", kingdom: "wei", skill: "刚烈" },
  "zhangliao": { name: "张辽", kingdom: "wei", skill: "突袭" },
  "xuchu": { name: "许褚", kingdom: "wei", skill: "裸衣" },
  "zhenji": { name: "甄姬", kingdom: "wei", skill: "洛神 / 倾国" },
  
  "liubei": { name: "刘备", kingdom: "shu", skill: "仁德 / 激将" },
  "guanyu": { name: "关羽", kingdom: "shu", skill: "武圣" },
  "zhangfei": { name: "张飞", kingdom: "shu", skill: "咆哮" },
  "zhugeliang": { name: "诸葛亮", kingdom: "shu", skill: "观星 / 空城" },
  "zhaoyun": { name: "赵云", kingdom: "shu", skill: "龙胆" },
  "machao": { name: "马超", kingdom: "shu", skill: "马术 / 铁骑" },
  "huangyueying": { name: "黄月英", kingdom: "shu", skill: "集智 / 奇才" },
  
  "sunquan": { name: "孙权", kingdom: "wu", skill: "制衡 / 救援" },
  "ganning": { name: "甘宁", kingdom: "wu", skill: "奇袭" },
  "lvmeng": { name: "吕蒙", kingdom: "wu", skill: "克己" },
  "huanggai": { name: "黄盖", kingdom: "wu", skill: "苦肉" },
  "zhouyu": { name: "周瑜", kingdom: "wu", skill: "英姿 / 反间" },
  "daqiao": { name: "大乔", kingdom: "wu", skill: "国色 / 流离" },
  "luxun": { name: "陆逊", kingdom: "wu", skill: "谦逊 / 连营" },
  "sunshangxiang": { name: "孙尚香", kingdom: "wu", skill: "结姻 / 枭姬" },
  
  "huatuo": { name: "华佗", kingdom: "qun", skill: "青囊 / 急救" },
  "lvbu": { name: "吕布", kingdom: "qun", skill: "无双" },
  "diaochan": { name: "貂蝉", kingdom: "qun", skill: "离间 / 闭月" },
  "yuanshu": { name: "袁术", kingdom: "qun", skill: "庸肆 / 伪帝" },
  "huaxiong": { name: "华雄", kingdom: "qun", skill: "耀武 / 负勇" }
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

const getInfo = (id) => generalMap[id] || { name: id, kingdom: "god", skill: "未知技能" };

</script>

<template>
  <div class="selector-overlay">
    
    <div class="scroll-board">
      <div class="scroll-roller left"></div>
      <div class="scroll-roller right"></div>

      <div class="scroll-content">
        <h2 class="title-seal">奉 旨 点 将</h2>
        
        <div class="cards-row">
          <div 
            v-for="id in candidates" 
            :key="id" 
            class="general-card-large"
            :class="[getInfo(id).kingdom, { active: selectedId === id }]"
            @click="handleSelect(id)"
          >
            <div class="bg-char">{{ getInfo(id).kingdom[0].toUpperCase() }}</div>
            
            <div class="card-inner">
              <div class="kingdom-badge">{{ getInfo(id).kingdom.toUpperCase() }}</div>
              <div class="general-name">{{ getInfo(id).name }}</div>
              
              <div class="skill-box">
                <div class="skill-title">技能</div>
                <div class="skill-text">{{ getInfo(id).skill }}</div>
              </div>
              
              <div v-if="selectedId === id" class="select-mark">
                <span>选</span>
              </div>
            </div>
          </div>
        </div>

        <div class="action-footer">
          <button 
            class="btn-confirm-seal" 
            :disabled="!selectedId"
            @click="confirmSelection"
          >
            确 认 登 场
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 遮罩 */
.selector-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.85);
  backdrop-filter: blur(8px);
  z-index: 2000;
  display: flex; justify-content: center; align-items: center;
}

/* 卷轴板 */
.scroll-board {
  position: relative;
  width: 800px;
  height: 500px;
  background-color: #fdfbf7; /* 宣纸色 */
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23d6d3c7' fill-opacity='0.4'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7z' /%3E%3C/g%3E%3C/svg%3E");
  box-shadow: 0 20px 60px rgba(0,0,0,0.8);
  display: flex; flex-direction: column;
  padding: 10px 40px;
}

/* 卷轴两侧的轴 */
.scroll-roller {
  position: absolute; top: -20px; bottom: -20px; width: 30px;
  background: linear-gradient(to right, #5d4037, #3e2723, #271c19);
  border: 1px solid #1a1a1a;
  border-radius: 4px;
  box-shadow: 5px 0 15px rgba(0,0,0,0.6);
}
.scroll-roller.left { left: -15px; }
.scroll-roller.right { right: -15px; }
/* 轴头装饰 */
.scroll-roller::before, .scroll-roller::after {
  content: ''; position: absolute; left: -5px; width: 40px; height: 25px;
  background: radial-gradient(circle, #e6b0aa, #8d6e63);
  border-radius: 4px; border: 1px solid #3e2723;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
}
.scroll-roller::before { top: -10px; }
.scroll-roller::after { bottom: -10px; }

/* 内容区 */
.scroll-content {
  flex: 1; display: flex; flex-direction: column; align-items: center;
}

.title-seal {
  font-family: 'LiSu', serif;
  font-size: 42px;
  color: var(--sgs-red, #c0392b);
  border: 4px solid var(--sgs-red, #c0392b);
  padding: 5px 25px;
  margin: 20px 0 40px 0;
  border-radius: 8px;
  letter-spacing: 10px;
  text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
  box-shadow: inset 0 0 10px rgba(192, 57, 43, 0.2);
}

.cards-row {
  display: flex; gap: 40px; justify-content: center; width: 100%;
}

/* === 武将大卡 === */
.general-card-large {
  width: 180px; height: 260px;
  background: #2c3e50;
  border: 4px solid #555;
  border-radius: 8px;
  position: relative;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  overflow: hidden;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

/* 势力配色 */
.general-card-large.wei { border-color: #2980b9; background: linear-gradient(135deg, #154360, #2980b9); }
.general-card-large.shu { border-color: #c0392b; background: linear-gradient(135deg, #641e16, #c0392b); }
.general-card-large.wu { border-color: #27ae60; background: linear-gradient(135deg, #145a32, #27ae60); }
.general-card-large.qun { border-color: #7f8c8d; background: linear-gradient(135deg, #424949, #7f8c8d); }

/* 背景大字 */
.bg-char {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-size: 140px; font-family: 'LiSu'; color: rgba(255,255,255,0.15);
  font-weight: bold; pointer-events: none;
}

.card-inner {
  height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: space-between;
  padding: 15px; position: relative; z-index: 2;
}

.kingdom-badge {
  font-size: 14px; color: rgba(255,255,255,0.8); border: 1px solid rgba(255,255,255,0.5);
  padding: 1px 6px; border-radius: 4px; align-self: flex-start;
}

.general-name {
  font-family: 'STKaiti', serif; font-size: 36px; color: #fff;
  text-shadow: 0 2px 5px rgba(0,0,0,0.8); font-weight: bold;
  writing-mode: vertical-rl; letter-spacing: 5px;
  flex: 1; display: flex; align-items: center; justify-content: center;
}

.skill-box {
  width: 100%; background: rgba(0,0,0,0.6); padding: 8px; border-radius: 4px;
}
.skill-title { font-size: 10px; color: #aaa; margin-bottom: 2px; }
.skill-text { font-size: 12px; color: #f1c40f; text-align: center; }

/* 选中状态 */
.general-card-large.active {
  transform: translateY(-15px) scale(1.05);
  border-color: #f1c40f;
  box-shadow: 0 0 30px rgba(241, 196, 15, 0.6);
}
.select-mark {
  position: absolute; top: 10px; right: 10px;
  width: 30px; height: 30px; background: #27ae60; color: #fff;
  border-radius: 50%; display: flex; justify-content: center; align-items: center;
  font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.5);
}

/* === 底部按钮 === */
.action-footer { margin-top: 30px; }

.btn-confirm-seal {
  background: linear-gradient(to bottom, #f39c12, #d35400);
  border: 2px solid #a04000;
  color: #fff;
  padding: 12px 50px;
  font-size: 24px;
  font-family: 'LiSu', serif;
  border-radius: 50px;
  cursor: pointer;
  box-shadow: 0 5px 15px rgba(211, 84, 0, 0.4);
  transition: all 0.2s;
}
.btn-confirm-seal:hover:not(:disabled) {
  transform: scale(1.05); filter: brightness(1.1);
}
.btn-confirm-seal:disabled {
  background: #95a5a6; border-color: #7f8c8d; cursor: not-allowed;
}
</style>