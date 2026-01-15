import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, select  # <--- 新增

# === 引用 ===
from app.core.database import create_db_and_tables, engine # <--- 新增 engine 引用
from app.api.auth import router as auth_router
from app.core.security import decode_access_token
from app.models.user import User      # <--- 新增 User 模型引用

from app.game.manager import room_manager
from app.game.room import GamePhase

# === 1. 初始化服务架构 ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    print("✅ 数据库表结构已初始化")
    yield

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/api/auth", tags=["用户认证"])

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
    return {"status": "ok", "version": "SGS Hardcore Engine v4.2 (Nickname Fix)"}

# === 2. 状态同步与系统通知工具 ===

async def broadcast_room_state(room):
    state = room.get_public_state()
    
    if state["phase"] == GamePhase.GAME_OVER and room.winner_sid:
        winner = room.get_player(room.winner_sid)
        if winner:
            winner_name = winner.nickname if winner.nickname != "无名氏" else f"{winner.seat_id}号位"
            await notify_room(room.room_id, f"🏆 游戏结束！胜利者是：{winner_name}")

    await sio.emit('room_update', state, room=room.room_id)
    
    for p in room.players:
        if p.is_alive:
            cards_data = [c.model_dump() for c in p.hand_cards]
            await sio.emit('hand_update', {'cards': cards_data}, room=p.sid)

async def notify_error(sid, msg):
    await sio.emit('system_message', {'msg': f"❌ {msg}"}, room=sid)

async def notify_room(room_id, msg):
    await sio.emit('system_message', {'msg': msg}, room=room_id)

# === 3. 基础房间管理事件 ===

@sio.event
async def connect(sid, environ, auth=None):
    """
    连接时查询数据库，获取完整用户信息并存入 Session
    """
    user_info = {"nickname": "无名氏", "avatar": "default.png", "username": ""}
    
    if auth and "token" in auth:
        token = auth["token"]
        username = decode_access_token(token)
        if username:
            # 🌟 关键修改：去数据库查完整信息
            with Session(engine) as db:
                statement = select(User).where(User.username == username)
                user = db.exec(statement).first()
                if user:
                    user_info = {
                        "username": user.username,
                        "nickname": user.nickname,
                        "avatar": user.avatar
                    }
                    print(f"🔐 用户已认证: {user.nickname} (@{user.username})")
                else:
                    print(f"⚠️ Token有效但用户不存在: {username}")
        else:
            print(f"⚠️ Token 无效/过期: {sid}")
    else:
        print(f"👤 游客连接: {sid}")

    # 将查到的信息存入 Socket 会话，供后续 join_room 使用
    await sio.save_session(sid, user_info)

@sio.event
async def disconnect(sid):
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
    room_id = data.get("room_id")
    if not room_id:
        return await notify_error(sid, "请输入合法的房间号")

    room = room_manager.create_room(room_id)
    
    # 🌟 关键修改：从 Session 取出刚才存的用户信息
    session = await sio.get_session(sid)
    user_info = session if session else {}
    
    # 将 user_info 传递给 add_player (下一步我们需要修改 room.py 来接收它)
    success, msg = room.add_player(sid, user_info)
    
    if not success:
        return await notify_error(sid, msg)

    nickname = user_info.get("nickname", "未知玩家")
    await sio.enter_room(sid, room_id)
    await notify_room(room_id, f"玩家 [{nickname}] 进入了房间")
    await broadcast_room_state(room)

@sio.event
async def toggle_ready(sid, data):
    room = room_manager.get_player_room(sid)
    if room and not room.is_started:
        room.toggle_ready(sid)
        await broadcast_room_state(room)

@sio.event
async def kick_player(sid, data):
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
    room = room_manager.get_player_room(sid)
    if not room: return
    success, msg = room.start_game()
    if success:
        await sio.emit('game_started', {}, room=room.room_id)
        await notify_room(room.room_id, "⚔️ 乱世开启，各显神通！")
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)

# === 核心战斗与响应逻辑 (保持不变) ===

@sio.event
async def play_card(sid, data):
    room = room_manager.get_player_room(sid)
    if not room: return
    idx = data.get("card_index")
    target = data.get("target_sid")
    success, msg, card = room.play_card(sid, idx, target)
    if not success: return await notify_error(sid, msg)

    await sio.emit('player_played', {
        "player_id": sid,
        "target_id": target,
        "card": card.model_dump()
    }, room=room.room_id)

    p_src = room.get_player(sid)
    src_name = p_src.nickname # 使用昵称播报
    if card.name == "杀":
        p_target = room.get_player(target)
        await notify_room(room.room_id, f"⚔️ {src_name} 对 {p_target.nickname} 发起攻击")
    elif card.name == "顺手牵羊":
        await notify_room(room.room_id, f"🤏 {src_name} 正在实施【顺手牵羊】")
    elif card.name == "过河拆桥":
        await notify_room(room.room_id, f"🧨 {src_name} 正在实施【过河拆桥】")
    else:
        await notify_room(room.room_id, f"{src_name} 打出: {card.name}")

    await broadcast_room_state(room)

@sio.event
async def respond_action(sid, data):
    room = room_manager.get_player_room(sid)
    if not room: return
    index = data.get("card_index")
    area = data.get("target_area")
    success, msg = room.handle_response(sid, index, area)
    if success:
        await notify_room(room.room_id, f"📢 {msg}")
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)

@sio.event
async def end_turn(sid, data):
    room = room_manager.get_player_room(sid)
    if not room: return
    success, msg = room.try_end_turn(sid)
    if success:
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)