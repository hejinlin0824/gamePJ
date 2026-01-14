import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.game.manager import room_manager
from app.game.room import GamePhase

# === 1. 初始化服务 ===
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
async def root():
    return {"status": "ok", "msg": "SGS Multi-Room Server Online"}

# === 2. 状态同步助手 ===

async def broadcast_room_state(room):
    """同步房间公共状态和每个人的私有手牌"""
    # 1. 广播房间公共信息 (含准备状态、房主信息等)
    await sio.emit('room_update', room.get_public_state(), room=room.room_id)
    
    # 2. 定向发送私有手牌
    for p in room.players:
        if p.is_alive:
            cards_data = [c.model_dump() for c in p.hand_cards]
            await sio.emit('hand_update', {'cards': cards_data}, room=p.sid)

async def notify_error(sid, msg):
    """向特定玩家发送红色错误提示"""
    await sio.emit('system_message', {'msg': f"❌ {msg}"}, room=sid)

async def notify_room(room_id, msg):
    """向整个房间发送系统通知"""
    await sio.emit('system_message', {'msg': msg}, room=room_id)

# === 3. Socket 事件处理 ===

@sio.event
async def connect(sid, environ):
    print(f"🔗 连入: {sid}")

@sio.event
async def disconnect(sid):
    """处理意外断开"""
    room = room_manager.get_player_room(sid)
    if room:
        room.remove_player(sid)
        await sio.leave_room(sid, room.room_id)
        if not room.players:
            room_manager.remove_room(room.room_id)
        else:
            await broadcast_room_state(room)

@sio.event
async def join_room(sid, data):
    room_id = data.get("room_id")
    if not room_id: return

    room = room_manager.create_room(room_id)
    success, msg = room.add_player(sid)
    
    if not success:
        return await notify_error(sid, msg)

    # 1. 玩家加入 SocketIO 房间
    await sio.enter_room(sid, room_id)
    
    # 2. 🌟 核心修复：先给当前玩家单独发一份状态，确保他能立即跳转
    await sio.emit('room_update', room.get_public_state(), room=sid)
    
    # 3. 再给房间所有人广播（同步人数变化）
    await broadcast_room_state(room)
    print(f"👤 玩家 {sid} 成功进入房间 {room_id}")

# --- 🌟 核心：准备与踢人逻辑 ---

@sio.event
async def toggle_ready(sid, data):
    """切换准备状态"""
    room = room_manager.get_player_room(sid)
    if room and not room.is_started:
        room.toggle_ready(sid)
        await broadcast_room_state(room)

@sio.event
async def kick_player(sid, data):
    """房主踢人逻辑"""
    target_sid = data.get("target_sid")
    room = room_manager.get_player_room(sid)
    
    if room and target_sid:
        success, msg = room.kick_player(sid, target_sid)
        if success:
            # 1. 通知被踢者离开
            await sio.emit('system_message', {'msg': '你已被房主踢出房间'}, room=target_sid)
            await sio.emit('kicked', {}, room=target_sid) # 触发前端重置
            await sio.leave_room(target_sid, room.room_id)
            # 2. 通知房间其他人
            await notify_room(room.room_id, "一名玩家被房主踢出")
            await broadcast_room_state(room)
        else:
            await notify_error(sid, msg)

@sio.event
async def start_game(sid, data):
    """开始游戏 (仅限房主且全员准备)"""
    room = room_manager.get_player_room(sid)
    if not room: return

    # 房主权限校验
    player = room.get_player(sid)
    if not player or not player.is_host:
        return await notify_error(sid, "只有房主可以开始游戏")

    # 内部会自动调用 can_start 检查准备情况
    success, msg = room.start_game()
    if success:
        await notify_room(room.room_id, "⚔️ 游戏正式开始！")
        await sio.emit('game_started', {}, room=room.room_id)
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)

# --- 游戏操作逻辑 ---

@sio.event
async def play_card(sid, data):
    """出牌请求"""
    room = room_manager.get_player_room(sid)
    if not room: return

    success, msg, card = room.play_card(sid, data.get("card_index"), data.get("target_sid"))
    if not success:
        return await notify_error(sid, msg)

    # 广播动画
    await sio.emit('player_played', {
        "player_id": sid,
        "target_id": data.get("target_sid"),
        "card": card.model_dump()
    }, room=room.room_id)

    # 简易效果结算
    if card.name == "杀":
        room.apply_damage(data.get("target_sid"), 1)
    elif card.name == "桃":
        p = room.get_player(sid)
        p.hp = min(p.hp + 1, p.max_hp)
    elif card.name == "无中生有":
        p = room.get_player(sid)
        p.hand_cards.extend(room.deck.draw(2))

    await broadcast_room_state(room)

@sio.event
async def end_turn(sid, data):
    """结束回合"""
    room = room_manager.get_player_room(sid)
    if not room: return

    success, msg = room.try_end_turn(sid)
    if success:
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)