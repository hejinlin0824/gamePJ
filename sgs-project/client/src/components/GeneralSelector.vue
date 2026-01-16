<script setup>
import { ref } from 'vue';

const props = defineProps({
  candidates: {
    type: Array, // ['caocao', 'zhaoyun', 'guojia']
    required: true
  }
});

const emit = defineEmits(['select']);

// 前端静态字典：用于将武将ID转为中文显示及技能预览
// (注：为了纯前端展示流畅，这里保留一份映射，实际项目中也可由后端传回详细对象)
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

// 获取头像地址 (兼容 Dicebear 和本地)
const getAvatarUrl = (id) => {
  // 这里假设本地没有图片，使用 Dicebear 生成随机头像
  // 实际项目中应替换为 `/generals/${id}.jpg`
  return `https://api.dicebear.com/7.x/adventurer/svg?seed=${id}&backgroundColor=b6e3f4,c0aede,d1d4f9`;
};

</script>

<template>
  <div class="selector-overlay">
    
    <div class="general-board">
      <div class="board-header">
        <div class="header-deco left"></div>
        <h2 class="title-text">奉 旨 点 将</h2>
        <div class="header-deco right"></div>
      </div>

      <div class="cards-container">
        <div 
          v-for="id in candidates" 
          :key="id" 
          class="general-option"
          :class="[getInfo(id).kingdom, { active: selectedId === id }]"
          @click="handleSelect(id)"
        >
          <div class="bg-kingdom-char">{{ getInfo(id).kingdom === 'god' ? '神' : getInfo(id).kingdom[0].toUpperCase() }}</div>
          
          <div class="card-content">
            <div class="kingdom-tag">{{ getInfo(id).kingdom.toUpperCase() }}</div>
            <div class="avatar-placeholder">
               <img :src="getAvatarUrl(id)" class="avatar-img" />
            </div>
            <div class="name-text">{{ getInfo(id).name }}</div>
            <div class="skill-preview">
              <span class="skill-label">技能:</span> {{ getInfo(id).skill }}
            </div>
          </div>

          <div v-if="selectedId === id" class="check-mark">✔</div>
        </div>
      </div>

      <div class="action-footer">
        <button 
          class="btn-confirm-seal" 
          :disabled="!selectedId"
          @click="confirmSelection"
        >
          <span>确</span><span>认</span><span>登</span><span>场</span>
        </button>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* 遮罩 */
.selector-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.9); /* 深色背景，聚焦视线 */
  backdrop-filter: blur(5px);
  z-index: 2000;
  display: flex; justify-content: center; align-items: center;
}

/* 主面板 */
.general-board {
  position: relative;
  width: 900px;
  max-width: 95%;
  background: #212121; /* 深灰底色 */
  border: 2px solid #5d4037;
  border-radius: 8px;
  box-shadow: 0 0 50px rgba(0,0,0,0.8);
  padding: 40px;
  display: flex; flex-direction: column; align-items: center;
  /* 木纹纹理 */
  background-image: repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 10px);
}

/* 标题栏 */
.board-header {
  display: flex; align-items: center; gap: 20px; margin-bottom: 40px;
}
.title-text {
  font-family: 'LiSu', serif;
  font-size: 48px;
  color: #f1c40f;
  margin: 0;
  text-shadow: 0 0 10px rgba(241, 196, 15, 0.5);
  letter-spacing: 10px;
}
.header-deco {
  height: 2px; width: 100px; background: linear-gradient(90deg, transparent, #f1c40f, transparent);
}

/* 卡牌容器 */
.cards-container {
  display: flex; gap: 30px; justify-content: center; width: 100%; flex-wrap: wrap;
}

/* 武将卡选项 */
.general-option {
  width: 160px; height: 240px;
  background: #333;
  border: 3px solid #555;
  border-radius: 8px;
  position: relative;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 10px 20px rgba(0,0,0,0.5);
}

/* 悬停效果 */
.general-option:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 30px rgba(0,0,0,0.7);
  border-color: #aaa;
}

/* 选中效果 */
.general-option.active {
  border-color: #f1c40f;
  transform: translateY(-10px) scale(1.05);
  box-shadow: 0 0 30px rgba(241, 196, 15, 0.4);
  z-index: 10;
}

/* 势力配色 (边框 & 背景微调) */
.general-option.wei { border-top-color: #2980b9; background: linear-gradient(160deg, #1a252f, #2c3e50); }
.general-option.shu { border-top-color: #c0392b; background: linear-gradient(160deg, #2c1b1b, #4a2323); }
.general-option.wu  { border-top-color: #27ae60; background: linear-gradient(160deg, #1b2e20, #254e32); }
.general-option.qun { border-top-color: #95a5a6; background: linear-gradient(160deg, #2c2c2c, #424242); }

/* 背景大字 */
.bg-kingdom-char {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  font-family: 'LiSu', serif;
  font-size: 100px;
  color: rgba(255,255,255,0.05);
  pointer-events: none;
  font-weight: bold;
}

/* 卡牌内容 */
.card-content {
  height: 100%; display: flex; flex-direction: column; align-items: center; padding: 10px;
  position: relative; z-index: 2;
}

.kingdom-tag {
  align-self: flex-start;
  font-size: 12px; color: #fff; opacity: 0.7; border: 1px solid rgba(255,255,255,0.3);
  padding: 1px 4px; border-radius: 2px;
}

.avatar-placeholder {
  width: 80px; height: 80px; margin: 15px 0;
  border-radius: 50%; border: 2px solid rgba(255,255,255,0.2);
  overflow: hidden; background: #000;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }

.name-text {
  font-family: 'LiSu', serif; font-size: 28px; color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,0.8);
  margin-bottom: 10px;
}

.skill-preview {
  font-size: 12px; color: #ccc; text-align: center; line-height: 1.4;
  background: rgba(0,0,0,0.3); padding: 5px; border-radius: 4px; width: 100%;
}
.skill-label { color: #f1c40f; }

/* 选中勾选标记 */
.check-mark {
  position: absolute; top: 5px; right: 5px;
  width: 24px; height: 24px; background: #f1c40f; color: #3e2723;
  border-radius: 50%; display: flex; justify-content: center; align-items: center;
  font-weight: bold; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  z-index: 5;
}

/* 底部按钮 */
.action-footer { margin-top: 50px; }

.btn-confirm-seal {
  background: linear-gradient(to bottom, #c0392b, #8e0000);
  border: 2px solid #5a0b0b;
  color: #fff;
  padding: 12px 60px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 5px 15px rgba(0,0,0,0.5);
  font-family: 'LiSu', serif;
  font-size: 24px;
  letter-spacing: 8px;
  transition: all 0.2s;
  display: flex; gap: 5px;
}

.btn-confirm-seal:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(192, 57, 43, 0.4);
  background: linear-gradient(to bottom, #e74c3c, #c0392b);
}

.btn-confirm-seal:disabled {
  background: #555; border-color: #333; color: #888;
  cursor: not-allowed; box-shadow: none;
}
</style>