from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# === 数据库配置 ===
# 使用 SQLite 文件型数据库，数据将存储在 server 根目录下的 database.db 文件中
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False 是 FastAPI 多线程环境下使用 SQLite 的必要配置
connect_args = {"check_same_thread": False}

# 创建数据库引擎
engine = create_engine(sqlite_url, connect_args=connect_args)

# === 工具函数 ===

def create_db_and_tables():
    """
    初始化数据库：读取所有继承自 SQLModel 的模型，并在数据库中创建对应的表。
    在 main.py 启动时调用此函数。
    """
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator:
    """
    FastAPI 依赖注入 (Dependency Injection) 使用的生成器。
    确保每个请求都有独立的数据库会话，并在请求结束后自动关闭。
    """
    with Session(engine) as session:
        yield session