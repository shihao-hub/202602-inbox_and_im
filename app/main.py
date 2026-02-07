from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, notifications
from app.api.v1.admin import admin_notifications

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="站内信与即时通讯系统 API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
app.include_router(
    notifications.router, prefix=f"{settings.API_V1_PREFIX}/notifications", tags=["站内信"]
)
app.include_router(
    admin_notifications.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["站内信管理"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用站内信与即时通讯系统 API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
