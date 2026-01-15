from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
import bcrypt  # <--- 核心修改：直接使用 bcrypt 库，不再通过 passlib 调用

# === 安全配置 ===
# ⚠️ 生产环境请修改 SECRET_KEY
SECRET_KEY = "CHANGE_THIS_TO_A_SUPER_SECRET_KEY_FOR_SGS_PROJECT"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希密码是否匹配"""
    # bcrypt.checkpw 需要 bytes 类型，但数据库里存的是 str
    if isinstance(hashed_password, str):
        hashed_password_bytes = hashed_password.encode('utf-8')
    else:
        hashed_password_bytes = hashed_password
    
    # 预防 bcrypt 库对空密码的处理
    if not plain_password:
        return False

    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password_bytes)
    except ValueError:
        # 防止无效 salt 导致崩溃
        return False

def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8') # 转回字符串以便存入 SQLite

def create_access_token(subject: Union[str, Any]) -> str:
    """
    生成 JWT 访问令牌
    :param subject: 主题，通常放入用户的 username 或 user_id
    """
    # 使用 timezone.utc 兼容 Python 3.14+ (utcnow 已被弃用)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Union[str, None]:
    """
    解码 JWT 令牌
    :return: 成功返回 username (sub)，失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except jwt.JWTError:
        return None