import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url' // 1. 引入 node 的 URL 处理模块

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  // 2. 新增 resolve 配置，定义 '@' 别名
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    hmr: {
       // 保持你之前的配置
    }
  }
})