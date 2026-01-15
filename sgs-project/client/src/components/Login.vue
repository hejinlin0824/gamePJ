<template>
  <div class="login-overlay">
    <div class="sgs-tablet">
      <div class="rivet top-left"></div>
      <div class="rivet top-right"></div>
      <div class="rivet bottom-left"></div>
      <div class="rivet bottom-right"></div>

      <h1 class="sgs-title">
        <span class="title-text">{{ isRegisterMode ? '新锐集结' : '逐鹿中原' }}</span>
      </h1>

      <div class="tab-switch">
        <div 
          class="tab-item left-tab" 
          :class="{ active: !isRegisterMode }"
          @click="toggleMode(false)"
        >
          登 录
        </div>
        <div 
          class="tab-item right-tab"
          :class="{ active: isRegisterMode }"
          @click="toggleMode(true)"
        >
          注 册
        </div>
      </div>

      <div class="form-content">
        <div class="input-group sgs-scroll-style">
          <label>账 号</label>
          <input type="text" v-model="form.username" placeholder="请输入主公名讳" />
        </div>

        <div class="input-group sgs-scroll-style">
          <label>密 码</label>
          <input type="password" v-model="form.password" placeholder="请输入密令" />
        </div>

        <div v-if="isRegisterMode" class="input-group sgs-scroll-style nickname-enter">
          <label>字 号</label>
          <input type="text" v-model="form.nickname" placeholder="行走江湖的名号" />
        </div>

        <div v-if="errorMsg" class="error-banner">
          ⚠️ {{ errorMsg }}
        </div>

        <button class="sgs-btn-confirm" @click="handleSubmit" :disabled="loading">
          <span v-if="!loading">{{ isRegisterMode ? '立誓参战' : '整军出发' }}</span>
          <span v-else>处理中...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/userStore'

const userStore = useUserStore()

// === 状态控制 ===
const isRegisterMode = ref(false) // false=登录, true=注册
const loading = ref(false)
const errorMsg = ref('')

// === 表单数据 ===
const form = reactive({
  username: '',
  password: '',
  nickname: ''
})

// === 切换模式 ===
const toggleMode = (mode) => {
  if (loading.value) return
  isRegisterMode.value = mode
  errorMsg.value = ''
  // 切换时清空密码，保留账号方便用户
  form.password = ''
  form.nickname = ''
}

// === 提交表单 ===
const handleSubmit = async () => {
  errorMsg.value = ''
  
  // 基础验证
  if (!form.username || !form.password) {
    errorMsg.value = '账号和密码乃立身之本，不可为空！'
    return
  }
  if (isRegisterMode.value && !form.nickname) {
    errorMsg.value = '行走江湖，怎能没有字号？'
    return
  }

  loading.value = true
  let result

  if (isRegisterMode.value) {
    // === 注册逻辑 ===
    result = await userStore.register(form.username, form.password, form.nickname)
    if (result.success) {
      alert("🎉 注册成功！请使用新账号登录。")
      toggleMode(false) // 切换回登录页
    } else {
      errorMsg.value = result.msg
    }
  } else {
    // === 登录逻辑 ===
    result = await userStore.login(form.username, form.password)
    if (result.success) {
      // 登录成功后的跳转逻辑由父组件控制（通常是关闭 Modal 或跳转页面）
      console.log("登录成功，用户信息已存入 Store")
    } else {
      errorMsg.value = result.msg
    }
  }
  
  loading.value = false
}
</script>

<style scoped>
/* === 整体容器风格 === */
.login-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.7); /* 深色背景遮罩 */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(3px);
}

.sgs-tablet {
  position: relative;
  width: 420px;
  /* 复杂的背景：模拟深色木纹+青铜边框 */
  background: 
    linear-gradient(to bottom, rgba(60, 40, 20, 0.9), rgba(40, 25, 15, 0.95)),
    url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjMmUxZTE1IiAvPgo8cmVjdCB3aWR0aD0iMSIgaGVpZ2h0PSIxIiBmaWxsPSIjNDMyYjIxIiAvPjwvc3ZnPg=='); /* 简单的噪点纹理 */
  border: 8px solid #2c1e15; /* 深棕色外边框 */
  box-shadow: 
    inset 0 0 20px rgba(0,0,0,0.8), /* 内阴影增加厚重感 */
    0 10px 30px rgba(0,0,0,0.5),   /* 外阴影增加悬浮感 */
    0 0 0 2px #5e452b;             /* 极细的金/铜色描边 */
  border-radius: 12px;
  padding: 30px 25px;
  color: #d4af37; /* 古金色文字 */
}

/* === 装饰性铆钉 === */
.rivet {
  position: absolute;
  width: 16px;
  height: 16px;
  background: radial-gradient(circle at 30% 30%, #d4af37, #5e452b 60%, #2c1e15 100%);
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.6);
}
.top-left { top: 10px; left: 10px; }
.top-right { top: 10px; right: 10px; }
.bottom-left { bottom: 10px; left: 10px; }
.bottom-right { bottom: 10px; right: 10px; }

/* === 标题 === */
.sgs-title {
  text-align: center;
  margin: 0 0 25px 0;
  font-size: 32px;
  font-weight: bold;
  /* 模拟金属文字效果 */
  background: linear-gradient(to bottom, #fff0a0, #d4af37, #8c6221);
  -webkit-background-clip: text;
  color: transparent;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  font-family: "STKaiti", "KaiTi", serif; /* 尝试使用楷体，如果没有则回退 */
}

/* === 切换标签 (Tab Switch) === */
.tab-switch {
  display: flex;
  margin-bottom: 25px;
  border-bottom: 3px solid #4e3422;
  position: relative;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 12px 0;
  font-size: 18px;
  cursor: pointer;
  background: #2a1b12; /* 未选中状态：暗沉木色 */
  color: #886644;
  border-top: 2px solid #3e2b1f;
  border-left: 2px solid #3e2b1f;
  border-right: 2px solid #3e2b1f;
  border-radius: 8px 8px 0 0;
  transition: all 0.3s ease;
}

.tab-item.active {
  background: linear-gradient(to bottom, #5e452b, #3e2b1f); /* 选中状态：亮木色 */
  color: #ffcc00; /* 亮金色 */
  font-weight: bold;
  border-top: 2px solid #d4af37;
  box-shadow: 0 -4px 10px rgba(212, 175, 55, 0.2);
  transform: translateY(-2px); /* 微微抬起 */
}

/* === 表单输入 === */
.input-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.input-group label {
  font-size: 16px;
  margin-bottom: 8px;
  color: #e0c080;
}

/* 模拟卷轴/古纸的输入框 */
.sgs-scroll-style input {
  background: #f4e7b3; /* 陈旧纸张色 */
  border: 3px solid #3e2b1f; /* 深棕粗边框 */
  border-radius: 4px;
  padding: 12px 15px;
  font-size: 16px;
  color: #3e2b1f;
  font-weight: bold;
  box-shadow: inset 0 3px 8px rgba(0,0,0,0.2); /* 内部凹陷感 */
  transition: border-color 0.3s;
}
.sgs-scroll-style input:focus {
  outline: none;
  border-color: #d4af37; /* 聚焦时变金色 */
  background: #fff8e0;
}

/* === 按钮：朱砂印章 === */
.sgs-btn-confirm {
  width: 100%;
  padding: 14px;
  font-size: 20px;
  font-weight: bold;
  color: #fff0a0;
  /* 模拟朱砂红印章 */
  background: linear-gradient(to bottom, #c0392b, #8b0000);
  border: 3px solid #5a1a1a;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 
    inset 0 2px 4px rgba(255,255,255,0.2), /* 顶部高光 */
    0 4px 8px rgba(0,0,0,0.5); /* 底部阴影 */
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  transition: all 0.1s;
}

.sgs-btn-confirm:hover:not(:disabled) {
  background: linear-gradient(to bottom, #e74c3c, #c0392b);
  transform: translateY(-1px);
  box-shadow: 
    inset 0 2px 4px rgba(255,255,255,0.3),
    0 6px 12px rgba(0,0,0,0.6);
}

.sgs-btn-confirm:active:not(:disabled) {
  transform: translateY(2px); /* 按下效果 */
  box-shadow: inset 0 4px 8px rgba(0,0,0,0.4);
  background: linear-gradient(to bottom, #8b0000, #a93226);
}
.sgs-btn-confirm:disabled {
  background: #5a3a3a;
  color: #aaa;
  border-color: #3a2a2a;
  cursor: not-allowed;
}

/* === 错误横幅 === */
.error-banner {
  background: rgba(139, 0, 0, 0.8);
  color: #ffcccc;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
  font-size: 14px;
  border-left: 4px solid #ff0000;
  animation: shake 0.4s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* 注册昵称出现的动画 */
.nickname-enter {
  animation: slideIn 0.3s ease-out;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>