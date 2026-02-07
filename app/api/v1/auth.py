from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_refresh_token
from app.dependencies import get_current_user
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    - **username**: 用户名（3-50 字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少 6 字符）
    """
    return AuthService.register(db, user_create)


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    - **username**: 用户名或邮箱
    - **password**: 密码

    返回 Access Token 和 Refresh Token
    """
    return AuthService.login(db, user_login.username, user_login.password)


@router.post("/refresh", response_model=Token)
async def refresh(token: str, db: Session = Depends(get_db)):
    """
    刷新 Token

    - **token**: Refresh Token

    返回新的 Access Token 和 Refresh Token
    """
    payload = verify_refresh_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Refresh Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    return AuthService.refresh(db, user_id)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    需要在 Header 中提供有效的 Access Token:
    - **Authorization**: Bearer <access_token>
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出

    需要在 Header 中提供有效的 Access Token
    客户端应删除本地存储的 Token

    注意：由于使用无状态 JWT，服务端无法主动使 Token 失效
    客户端应自行删除 Token 以实现登出效果
    """
    return {"message": "登出成功，请删除客户端 Token"}
