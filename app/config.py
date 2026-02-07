from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用信息
    APP_NAME: str = Field(default="站内信与即时通讯系统", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 路径前缀")

    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="服务器地址")
    PORT: int = Field(default=8000, description="服务器端口")

    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/inbox_im",
        description="数据库连接 URL",
    )
    DB_ECHO: bool = Field(default=False, description="是否输出 SQL 日志")

    # JWT 配置
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-this-in-production-min-32-chars",
        description="JWT 密钥（生产环境必须更改）",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access Token 有效期（分钟）")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh Token 有效期（天）")

    # CORS 配置
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="允许的 CORS 源",
    )

    # 密码加密
    PASSWORD_BCRYPT_ROUNDS: int = Field(default=12, description="密码加密 rounds")

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """获取 CORS 源列表"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS


settings = Settings()
