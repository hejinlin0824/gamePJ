import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.game.manager import room_manager
from app.game.room import GamePhase

# === 1. 初始化服务架构 ===

# 创建异步 Socket.IO 服务器，允许跨域
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# 跨域中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载应用
socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
async def root():
    return {"status": "ok", "version": "SGS Hardcore Engine v4.0 (Win/Loss & Snatch Update)"}

# === 2. 状态同步与系统通知工具 ===

async def broadcast_room_state(room):
    """
    核心同步函数：
    1. 刷新公共状态（包括胜利者判定 winner_sid）
    2. 私发手牌更新
    """
    # 获取全量公共状态
    state = room.get_public_state()
    
    # 如果游戏结束，发送胜利通告
    if state["phase"] == GamePhase.GAME_OVER and room.winner_sid:
        winner = room.get_player(room.winner_sid)
        if winner:
            await notify_room(room.room_id, f"🏆 游戏结束！胜利者是：{winner.seat_id}号位")

    # 广播公共数据
    await sio.emit('room_update', state, room=room.room_id)
    
    # 私发手牌数据（确保安全）
    for p in room.players:
        if p.is_alive:
            cards_data = [c.model_dump() for c in p.hand_cards]
            await sio.emit('hand_update', {'cards': cards_data}, room=p.sid)

async def notify_error(sid, msg):
    """私发错误消息提示"""
    await sio.emit('system_message', {'msg': f"❌ {msg}"}, room=sid)

async def notify_room(room_id, msg):
    """向全房间广播系统消息"""
    await sio.emit('system_message', {'msg': msg}, room=room_id)

# === 3. 基础房间管理事件 ===

@sio.event
async def connect(sid, environ):
    print(f"🔗 玩家连接成功: {sid}")

@sio.event
async def disconnect(sid):
    """处理玩家掉线及房间清理"""
    room = room_manager.get_player_room(sid)
    if room:
        room.remove_player(sid)
        await sio.leave_room(sid, room.room_id)
        if not room.players:
            room_manager.remove_room(room.room_id)
        else:
            await notify_room(room.room_id, "一名玩家离开了战场")
            await broadcast_room_state(room)

@sio.event
async def join_room(sid, data):
    """加入房间并绑定频道"""
    room_id = data.get("room_id")
    if not room_id:
        return await notify_error(sid, "请输入合法的房间号")

    room = room_manager.create_room(room_id)
    success, msg = room.add_player(sid)
    
    if not success:
        return await notify_error(sid, msg)

    await sio.enter_room(sid, room_id)
    await notify_room(room_id, f"新玩家进入了房间")
    await broadcast_room_state(room)

@sio.event
async def toggle_ready(sid, data):
    """玩家准备/取消准备"""
    room = room_manager.get_player_room(sid)
    if room and not room.is_started:
        room.toggle_ready(sid)
        await broadcast_room_state(room)

@sio.event
async def kick_player(sid, data):
    """房主踢人权限"""
    target_sid = data.get("target_sid")
    room = room_manager.get_player_room(sid)
    
    if room and target_sid:
        success, msg = room.kick_player(sid, target_sid)
        if success:
            await sio.emit('kicked', {}, room=target_sid)
            await sio.leave_room(target_sid, room.room_id)
            await broadcast_room_state(room)
        else:
            await notify_error(sid, msg)

@sio.event
async def start_game(sid, data):
    """开始游戏初始化"""
    room = room_manager.get_player_room(sid)
    if not room: return

    success, msg = room.start_game()
    if success:
        await sio.emit('game_started', {}, room=room.room_id)
        await notify_room(room.room_id, "⚔️ 乱世开启，各显神通！")
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)

# === 🌟 核心战斗与响应结算逻辑 ===

@sio.event
async def play_card(sid, data):
    """
    玩家主动出牌
    data: { "card_index": int, "target_sid": str }
    """
    room = room_manager.get_player_room(sid)
    if not room: return

    idx = data.get("card_index")
    target = data.get("target_sid")

    # 调用核心规则层逻辑
    success, msg, card = room.play_card(sid, idx, target)
    
    if not success:
        return await notify_error(sid, msg)

    # 广播动画同步
    await sio.emit('player_played', {
        "player_id": sid,
        "target_id": target,
        "card": card.model_dump()
    }, room=room.room_id)

    # 消息播报
    p_src = room.get_player(sid)
    if card.name == "杀":
        p_target = room.get_player(target)
        await notify_room(room.room_id, f"⚔️ {p_src.seat_id}号位 对 {p_target.seat_id}号位 发起攻击")
    elif card.name == "顺手牵羊":
        await notify_room(room.room_id, f"🤏 {p_src.seat_id}号位 正在对目标实施【顺手牵羊】")
    elif card.name == "过河拆桥":
        await notify_room(room.room_id, f"🧨 {p_src.seat_id}号位 正在对目标实施【过河拆桥】")
    else:
        await notify_room(room.room_id, f"打出卡牌: {card.name}")

    await broadcast_room_state(room)

@sio.event
async def respond_action(sid, data):
    """
    🌟 处理询问响应：包含顺手牵羊的最终结算通告
    data: { "card_index": int, "target_area": str }
    """
    room = room_manager.get_player_room(sid)
    if not room: return

    index = data.get("card_index")
    area = data.get("target_area")

    # 执行响应逻辑（在此阶段会发生：顺手牵羊拿牌、拆桥丢牌、杀掉血）
    success, msg = room.handle_response(sid, index, area)
    
    if success:
        await notify_room(room.room_id, f"📢 {msg}")
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)

@sio.event
async def end_turn(sid, data):
    """玩家手动结束回合"""
    room = room_manager.get_player_room(sid)
    if not room: return

    success, msg = room.try_end_turn(sid)
    if success:
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)