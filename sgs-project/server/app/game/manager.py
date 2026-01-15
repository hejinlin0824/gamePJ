from typing import Dict, Optional, List
from .room import GameRoom

class RoomManager:
    def __init__(self):
        # 存储所有活跃房间: { "101": GameRoom对象 }
        self.rooms: Dict[str, GameRoom] = {}

    def create_room(self, room_id: str) -> GameRoom:
        if room_id not in self.rooms:
            self.rooms[room_id] = GameRoom(room_id)
            print(f"🏠 创建新房间: {room_id}")
        return self.rooms[room_id]

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str):
        if room_id in self.rooms:
            del self.rooms[room_id]

    def get_player_room(self, sid: str) -> Optional[GameRoom]:
        """查找玩家当前所在的房间"""
        for room in self.rooms.values():
            if room.get_player(sid):
                return room
        return None

    # 🌟 新增：获取大厅列表数据 (默认 1-20 号房)
    def get_lobby_info(self) -> List[Dict]:
        lobby_list = []
        # 默认展示 20 个房间
        for i in range(1, 21):
            rid = str(i) # 房间号 "1", "2"... "20"
            room = self.rooms.get(rid)
            
            if room:
                lobby_list.append({
                    "room_id": rid,
                    "status": "playing" if room.is_started else "waiting",
                    "count": len(room.players),
                    "max_count": 8
                })
            else:
                # 房间未创建，视为空闲
                lobby_list.append({
                    "room_id": rid,
                    "status": "idle",
                    "count": 0,
                    "max_count": 8
                })
        return lobby_list

# 全局单例
room_manager = RoomManager()