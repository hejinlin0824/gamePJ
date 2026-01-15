from typing import Optional
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    # === 基础信息 ===
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)  # 登录账号，必须唯一
    hashed_password: str                            # 加密后的密码，不存储明文
    nickname: str                                   # 游戏昵称，显示在头像旁
    
    # === 游戏属性 ===
    avatar: str = "default.png"                     # 头像图片文件名
    level: int = 1                                  # 玩家等级
    exp: int = 0                                    # 当前经验值
    
    # === 战绩统计 ===
    wins: int = 0                                   # 胜利场次
    losses: int = 0                                 # 失败场次
    
    # 以后可以扩展更多字段，比如 vip_level, copper (铜钱) 等