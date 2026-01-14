from typing import Dict, Optional
from .room import GameRoom

class RoomManager:
    def __init__(self):
        # 存储所有房间: { "room_101": GameRoom对象 }
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

# 全局单例
room_manager = RoomManager()