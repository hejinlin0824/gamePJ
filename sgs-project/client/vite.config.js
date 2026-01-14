import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // <--- 关键：允许外部 IP 访问
    port: 5173,      // <--- 明确指定端口
    strictPort: true, // 如果端口被占用直接退出，不自动切到其他端口
    hmr: {
        // 如果你的服务器有复杂的反向代理，这里可能需要配置 clientPort
        // 暂时先保持默认，如果连上了但热更新失效再改
    }
  }
})