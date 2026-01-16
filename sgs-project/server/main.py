import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, select 

# === 引用 ===
from app.core.database import create_db_and_tables, engine 
from app.api.auth import router as auth_router
from app.core.security import decode_access_token
from app.models.user import User        

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
    return {"status": "ok", "version": "SGS Hardcore Engine v7.0 (Active Skills)"}

# === 2. 状态同步与系统通知工具 ===

async def broadcast_room_state(room):
    """向房间内所有玩家广播最新的游戏状态"""
    state = room.get_public_state()
    
    # 检查是否刚触发游戏结束
    if state["phase"] == GamePhase.GAME_OVER and room.winner_sid:
        winner = room.get_player(room.winner_sid)
        if winner:
            winner_name = winner.nickname if winner.nickname != "无名氏" else f"{winner.seat_id}号位"
            await notify_room(room.room_id, f"🏆 游戏结束！胜利者是：{winner_name}")

    await sio.emit('room_update', state, room=room.room_id)
    
    # 私有手牌数据单独发送 (安全机制)
    for p in room.players:
        if p.is_alive:
            # 序列化 Card 对象
            cards_data = [c.model_dump() for c in p.hand_cards]
            await sio.emit('hand_update', {'cards': cards_data}, room=p.sid)

async def notify_error(sid, msg):
    await sio.emit('system_message', {'msg': f"❌ {msg}"}, room=sid)

async def notify_room(room_id, msg):
    await sio.emit('system_message', {'msg': msg}, room=room_id)

async def broadcast_lobby():
    """向所有连接的客户端广播最新的大厅列表状态"""
    lobby_data = room_manager.get_lobby_info()
    await sio.emit('lobby_update', lobby_data)

# === 3. Socket 事件处理 ===

@sio.event
async def connect(sid, environ, auth=None):
    user_info = {"nickname": "无名氏", "avatar": "default.png", "username": ""}
    
    if auth and "token" in auth:
        token = auth["token"]
        username = decode_access_token(token)
        if username:
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
    
    if not user_info["username"]:
        print(f"⛔ 拒绝匿名/无效连接: {sid}")
        return False 

    await sio.save_session(sid, user_info)
    await broadcast_lobby()

@sio.event
async def disconnect(sid):
    """处理意外断开连接"""
    room = room_manager.get_player_room(sid)
    if room:
        if room.is_started:
            # 游戏进行中：触发逃跑逻辑，可能导致游戏结束
            msg = room.handle_disconnect_during_game(sid)
            await notify_room(room.room_id, msg)
            await sio.leave_room(sid, room.room_id)
            
            alive_players = [p for p in room.players if p.is_alive]
            
            if len(alive_players) == 0:
                print(f"💀 房间 {room.room_id} 无人生还，强制销毁")
                room_manager.remove_room(room.room_id)
            else:
                # 无论是否结束，都需要广播状态
                await broadcast_room_state(room)
        else:
            # 游戏未开始：正常离开
            room.remove_player(sid)
            await sio.leave_room(sid, room.room_id)
            
            if not room.players:
                print(f"🏠 房间 {room.room_id} 人去楼空，销毁")
                room_manager.remove_room(room.room_id)
            else:
                await notify_room(room.room_id, "一名玩家离开了战场")
                await broadcast_room_state(room)
    
    await broadcast_lobby()

@sio.event
async def join_room(sid, data):
    room_id = data.get("room_id")
    if not room_id: return await notify_error(sid, "请输入合法的房间号")

    room = room_manager.create_room(room_id)
    session = await sio.get_session(sid)
    user_info = session if session else {}
    
    success, msg = room.add_player(sid, user_info)
    if not success: return await notify_error(sid, msg)

    nickname = user_info.get("nickname", "未知玩家")
    await sio.enter_room(sid, room_id)
    await notify_room(room_id, f"玩家 [{nickname}] 进入了房间")
    
    await broadcast_room_state(room)
    await broadcast_lobby()

@sio.event
async def leave_room(sid, data):
    """前端主动点击“离开”按钮"""
    room = room_manager.get_player_room(sid)
    if room:
        if not room.is_started:
            room.remove_player(sid)
            await sio.leave_room(sid, room.room_id)
            if not room.players:
                room_manager.remove_room(room.room_id)
            else:
                await broadcast_room_state(room)
            await broadcast_lobby()
        else:
            # 游戏进行中逃跑逻辑
            print(f"👋 玩家 {sid} 主动点击离开按钮")
            msg = room.handle_disconnect_during_game(sid)
            await notify_room(room.room_id, msg)
            await sio.leave_room(sid, room.room_id)
            
            alive_players = [p for p in room.players if p.is_alive]
            if len(alive_players) == 0:
                room_manager.remove_room(room.room_id)
            else:
                await broadcast_room_state(room)
            
            await broadcast_lobby()

@sio.event
async def get_lobby(sid, data):
    lobby_data = room_manager.get_lobby_info()
    await sio.emit('lobby_update', lobby_data, room=sid)

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
            await broadcast_lobby()
        else:
            await notify_error(sid, msg)

@sio.event
async def start_game(sid, data):
    room = room_manager.get_player_room(sid)
    if not room: return
    success, msg = room.start_game()
    if success:
        await notify_room(room.room_id, msg)
        await broadcast_room_state(room)
        await broadcast_lobby()
    else:
        await notify_error(sid, msg)

@sio.event
async def select_general(sid, data):
    room = room_manager.get_player_room(sid)
    if not room: return
    general_id = data.get("general_id")
    if not general_id: return
    
    success, msg = room.select_general(sid, general_id)
    if success:
        await broadcast_room_state(room)
        if "游戏开始" in msg:
            await sio.emit('game_started', {}, room=room.room_id)
            await notify_room(room.room_id, "⚔️ 众将归位，乱世开启！")
        else:
            await sio.emit('system_message', {'msg': "✅ 武将选择已确认，等待他人..."}, room=sid)
    else:
        await notify_error(sid, msg)

@sio.event
async def play_card(sid, data):
    room = room_manager.get_player_room(sid)
    if not room: return
    
    idx = data.get("card_index")
    target = data.get("target_sid")
    
    success, msg, card = room.play_card(sid, idx, target)
    if not success: return await notify_error(sid, msg)

    # 广播打出的牌动画
    if card:
        await sio.emit('player_played', {
            "player_id": sid,
            "target_id": target,
            "card": card.model_dump()
        }, room=room.room_id)

    # 系统日志通知
    p_src = room.get_player(sid)
    src_name = p_src.nickname 
    if card.name == "杀":
        p_target = room.get_player(target)
        if p_target:
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
    """
    处理玩家的响应操作（出闪、弃牌、遗计分牌等）
    """
    room = room_manager.get_player_room(sid)
    if not room: return
    
    index = data.get("card_index")
    area = data.get("target_area")
    extra = data.get("extra_payload") # 🌟 核心：接收前端传来的复杂参数（如弃牌列表）
    
    success, msg = room.handle_response(sid, index, target_area=area, extra_payload=extra)
    if success:
        if msg:
            await notify_room(room.room_id, f"📢 {msg}")
        await broadcast_room_state(room)
    else:
        await notify_error(sid, msg)

@sio.event
async def use_skill(sid, data):
    """
    🌟 核心新增：处理主动技能释放 (如离间、青囊)
    """
    room = room_manager.get_player_room(sid)
    if not room: return
    
    skill_name = data.get("skill_name")
    targets = data.get("targets") or []
    card_indices = data.get("card_indices") or []
    
    success, msg = room.trigger_active_skill(sid, skill_name, targets, card_indices)
    
    if success:
        await notify_room(room.room_id, f"⚡ {msg}")
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