<script setup>
import { ref, reactive } from 'vue';
import { useUserStore } from '@/stores/userStore';

const userStore = useUserStore();

// === 状态控制 ===
const isRegisterMode = ref(false); // false=登录, true=注册
const loading = ref(false);
const errorMsg = ref('');

// === 表单数据 ===
const form = reactive({
  username: '',
  password: '',
  nickname: ''
});

// === 切换模式 ===
const toggleMode = (mode) => {
  if (loading.value) return;
  isRegisterMode.value = mode;
  errorMsg.value = '';
  // 切换时清空密码
  form.password = '';
  form.nickname = '';
};

// === 提交表单 ===
const handleSubmit = async () => {
  errorMsg.value = '';
  
  if (!form.username || !form.password) {
    errorMsg.value = '账号与密令不可为空！';
    return;
  }
  if (isRegisterMode.value && !form.nickname) {
    errorMsg.value = '行走乱世，岂能无名？';
    return;
  }

  loading.value = true;
  let result;

  if (isRegisterMode.value) {
    // 注册
    result = await userStore.register(form.username, form.password, form.nickname);
    if (result.success) {
      alert("🎉 注册成功！请使用新账号登录。");
      toggleMode(false);
    } else {
      errorMsg.value = result.msg;
    }
  } else {
    // 登录
    result = await userStore.login(form.username, form.password);
    if (result.success) {
      console.log("登录成功");
    } else {
      errorMsg.value = result.msg;
    }
  }
  
  loading.value = false;
};
</script>

<template>
  <div class="login-overlay">
    
    <div class="sgs-tablet">
      <div class="rivet top-left"></div>
      <div class="rivet top-right"></div>
      <div class="rivet bottom-left"></div>
      <div class="rivet bottom-right"></div>

      <h1 class="sgs-title">
        <span class="title-text">{{ isRegisterMode ? '新 锐 集 结' : '逐 鹿 中 原' }}</span>
      </h1>

      <div class="tab-switch">
        <div 
          class="tab-item" 
          :class="{ active: !isRegisterMode }"
          @click="toggleMode(false)"
        >
          登 录
        </div>
        <div 
          class="tab-item"
          :class="{ active: isRegisterMode }"
          @click="toggleMode(true)"
        >
          注 册
        </div>
      </div>

      <div class="form-content">
        <div class="input-group">
          <label>账 号</label>
          <input type="text" v-model="form.username" placeholder="请输入主公名讳" @keyup.enter="handleSubmit" />
        </div>

        <div class="input-group">
          <label>密 令</label>
          <input type="password" v-model="form.password" placeholder="请输入通关密令" @keyup.enter="handleSubmit" />
        </div>

        <transition name="slide-down">
          <div v-if="isRegisterMode" class="input-group">
            <label>字 号</label>
            <input type="text" v-model="form.nickname" placeholder="将军尊姓大名" @keyup.enter="handleSubmit" />
          </div>
        </transition>

        <div v-if="errorMsg" class="error-banner">
          ⚠️ {{ errorMsg }}
        </div>

        <div class="btn-container">
          <button class="sgs-seal-btn" @click="handleSubmit" :disabled="loading">
            <span v-if="!loading">{{ isRegisterMode ? '立誓参战' : '整军出发' }}</span>
            <span v-else>处理中...</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* === 整体遮罩 === */
.login-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.8); /* 深色背景 */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  backdrop-filter: blur(5px);
}

/* === 木质令牌容器 === */
.sgs-tablet {
  position: relative;
  width: 400px;
  /* 木纹材质 */
  background-color: var(--sgs-wood-dark, #3e2723);
  background-image: repeating-linear-gradient(135deg, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 2px, transparent 2px, transparent 8px);
  border: 4px solid #271c19;
  box-shadow: 
    inset 0 0 30px rgba(0,0,0,0.8), /* 内阴影增加厚重感 */
    0 20px 50px rgba(0,0,0,0.7),    /* 外阴影增加悬浮感 */
    0 0 0 2px #5e452b;              /* 极细的外描边 */
  border-radius: 12px;
  padding: 40px 30px;
  color: var(--sgs-gold, #ffb300);
}

/* === 铆钉装饰 === */
.rivet {
  position: absolute;
  width: 12px; height: 12px;
  background: radial-gradient(circle at 30% 30%, #ffd54f, #8d6e63);
  border-radius: 50%;
  box-shadow: 1px 1px 3px rgba(0,0,0,0.8);
}
.top-left { top: 10px; left: 10px; }
.top-right { top: 10px; right: 10px; }
.bottom-left { bottom: 10px; left: 10px; }
.bottom-right { bottom: 10px; right: 10px; }

/* === 标题 === */
.sgs-title {
  text-align: center;
  margin: 0 0 30px 0;
  font-size: 36px;
  font-weight: bold;
  font-family: 'LiSu', serif;
  color: var(--sgs-gold);
  text-shadow: 0 2px 4px rgba(0,0,0,0.8);
  border-bottom: 2px solid rgba(255,255,255,0.1);
  padding-bottom: 15px;
}

/* === 标签切换 === */
.tab-switch {
  display: flex;
  margin-bottom: 30px;
  background: rgba(0,0,0,0.3);
  border-radius: 6px;
  padding: 4px;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 10px 0;
  font-size: 18px;
  cursor: pointer;
  color: #8d6e63;
  transition: all 0.3s;
  font-family: 'LiSu', serif;
}

.tab-item.active {
  background: var(--sgs-wood-light);
  color: var(--sgs-paper);
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  text-shadow: 0 1px 2px #000;
}

/* === 输入框组 === */
.input-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.input-group label {
  font-size: 16px;
  margin-bottom: 8px;
  color: #d7ccc8;
  font-family: 'LiSu', serif;
}

.input-group input {
  background: var(--sgs-paper, #fdfbf7); /* 宣纸底色 */
  border: 2px solid #5d4037;
  border-radius: 4px;
  padding: 12px 15px;
  font-size: 18px;
  color: var(--sgs-ink, #212121); /* 墨色文字 */
  font-family: 'KaiTi', serif;
  font-weight: bold;
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.2);
  transition: border-color 0.3s;
  outline: none;
}

.input-group input:focus {
  border-color: var(--sgs-gold);
  background: #fff;
}

.input-group input::placeholder {
  color: #a1887f;
  font-weight: normal;
}

/* === 错误提示 === */
.error-banner {
  background: rgba(198, 40, 40, 0.2);
  color: #ff8a80;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
  font-size: 14px;
  border: 1px solid #e53935;
  text-align: center;
  animation: shake 0.4s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* === 印章按钮 === */
.btn-container {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}

.sgs-seal-btn {
  width: 100%;
  padding: 15px;
  font-size: 24px;
  font-weight: bold;
  font-family: 'LiSu', serif;
  color: #fff;
  /* 朱砂红印章 */
  background: linear-gradient(to bottom, #c62828, #b71c1c);
  border: 2px solid #8e0000;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 
    0 5px 10px rgba(0,0,0,0.5),
    inset 0 2px 5px rgba(255,255,255,0.2);
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  transition: all 0.1s;
  letter-spacing: 4px;
}

.sgs-seal-btn:hover:not(:disabled) {
  background: linear-gradient(to bottom, #e53935, #c62828);
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(0,0,0,0.6);
}

.sgs-seal-btn:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow: inset 0 3px 8px rgba(0,0,0,0.6);
}

.sgs-seal-btn:disabled {
  background: #5d4037;
  border-color: #3e2723;
  color: #8d6e63;
  cursor: not-allowed;
  box-shadow: none;
}

/* 动画：输入框滑入 */
.slide-down-enter-active {
  transition: all 0.3s ease-out;
}
.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}
</style>