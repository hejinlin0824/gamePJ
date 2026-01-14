import { io } from "socket.io-client";
import { reactive } from "vue";

// ⚠️ 重点：这里必须填你云服务器的【公网 IP】
// 如果填 localhost，浏览器会连你自己电脑，永远连不上服务器
const URL = "http://134.175.64.205:8005"; 

export const socketState = reactive({
  connected: false,
  fooEvents: [],
});

export const socket = io(URL, {
  autoConnect: false,
  transports: ["websocket"], // 强制使用 WebSocket 模式
});

socket.on("connect", () => {
  socketState.connected = true;
  console.log("✅ [Socket] 已连接:", socket.id);
});

socket.on("disconnect", () => {
  socketState.connected = false;
  console.log("❌ [Socket] 已断开");
});

socket.on("connect_error", (err) => {
  console.error("⚠️ [Socket] 连接错误:", err);
});

socket.onAny((event, ...args) => {
  console.log(`📩 [收包] ${event}`, args);
});