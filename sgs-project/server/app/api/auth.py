from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from pydantic import BaseModel

from app.core.database import get_session
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User

router = APIRouter()

# === 请求/响应数据模型 ===
# 专门用于注册请求的数据验证，不需要包含 id, wins 等内部字段
class UserCreate(BaseModel):
    username: str
    password: str
    nickname: str

# 登录成功后返回的数据结构
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    nickname: str
    avatar: str

# === 接口实现 ===

@router.post("/register", response_model=User)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    """
    用户注册接口
    """
    # 1. 检查用户名是否已存在
    statement = select(User).where(User.username == user_in.username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 2. 创建新用户 (密码加密存储)
    new_user = User(
        username=user_in.username,
        nickname=user_in.nickname,
        hashed_password=get_password_hash(user_in.password),
        avatar="default.png" # 默认头像
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """
    用户登录接口
    使用 OAuth2 标准表单 (username, password)
    """
    # 1. 查找用户
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    
    # 2. 校验密码
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. 生成 Token
    access_token = create_access_token(subject=user.username)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar
    }