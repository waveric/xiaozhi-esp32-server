"""
Web 管理界面认证模块
提供可选的用户名/密码认证，通过配置开关控制
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Callable

from fastapi import Request, HTTPException, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    token: Optional[str] = None
    message: str


# 内存存储的 token（单例）
_tokens: Dict[str, datetime] = {}

# 默认 token 过期时间
DEFAULT_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """生成密码 SHA256 hash"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    if not password_hash:
        return False
    return hash_password(password) == password_hash


def create_token(expire_hours: int = DEFAULT_TOKEN_EXPIRE_HOURS) -> str:
    """创建 token"""
    token = secrets.token_hex(32)
    _tokens[token] = datetime.now() + timedelta(hours=expire_hours)
    return token


def verify_token(token: str) -> bool:
    """验证 token，自动清理过期 token"""
    if token not in _tokens:
        return False
    if _tokens[token] < datetime.now():
        del _tokens[token]
        return False
    return True


def cleanup_expired_tokens() -> int:
    """清理所有过期 token，返回清理数量"""
    now = datetime.now()
    expired = [t for t, exp in _tokens.items() if exp < now]
    for t in expired:
        del _tokens[t]
    return len(expired)


class AuthManager:
    """认证管理器"""

    def __init__(self, config: dict):
        """
        初始化认证管理器

        Args:
            config: 配置字典，包含 web_auth 配置节
        """
        auth_config = config.get("web_auth", {})
        self.enabled = auth_config.get("enabled", False)
        self.username = auth_config.get("username", "admin")
        self.password_hash = auth_config.get("password_hash", "")
        self.token_expire_hours = auth_config.get("token_expire_hours", DEFAULT_TOKEN_EXPIRE_HOURS)

    def is_enabled(self) -> bool:
        """检查认证是否启用"""
        return self.enabled

    def login(self, username: str, password: str) -> LoginResponse:
        """
        登录验证

        Args:
            username: 用户名
            password: 密码

        Returns:
            LoginResponse: 登录结果
        """
        if not self.enabled:
            return LoginResponse(success=True, token=None, message="认证未启用")

        if username != self.username:
            return LoginResponse(success=False, message="用户名或密码错误")

        if not verify_password(password, self.password_hash):
            return LoginResponse(success=False, message="用户名或密码错误")

        token = create_token(self.token_expire_hours)
        return LoginResponse(success=True, token=token, message="登录成功")

    def check_auth(self, token: Optional[str]) -> bool:
        """
        检查认证状态

        Args:
            token: Bearer token

        Returns:
            bool: 是否认证通过
        """
        if not self.enabled:
            return True
        if not token:
            return False
        return verify_token(token)

    def get_auth_dependency(self) -> Callable:
        """
        获取 FastAPI 认证依赖

        Returns:
            认证依赖函数
        """
        if not self.enabled:
            # 认证关闭，直接通过
            async def no_auth():
                return None
            return no_auth

        # 认证开启
        security = HTTPBearer(auto_error=False)

        async def require_auth(
            request: Request,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            # 检查 cookie 中的 token（优先）
            cookie_token = request.cookies.get("auth_token")

            # 检查 Authorization header
            header_token = credentials.credentials if credentials else None

            token = cookie_token or header_token

            if not token or not verify_token(token):
                raise HTTPException(
                    status_code=401,
                    detail="未认证",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return token

        return require_auth

    def logout(self, token: str) -> bool:
        """
        登出（删除 token）

        Args:
            token: 要删除的 token

        Returns:
            bool: 是否成功删除
        """
        if token in _tokens:
            del _tokens[token]
            return True
        return False


def create_login_response(response: Response, login_result: LoginResponse) -> LoginResponse:
    """
    创建登录响应并设置 cookie

    Args:
        response: FastAPI Response 对象
        login_result: 登录结果

    Returns:
        LoginResponse: 登录结果
    """
    if login_result.success and login_result.token:
        # 设置 cookie（httpOnly 防止 XSS）
        response.set_cookie(
            key="auth_token",
            value=login_result.token,
            httponly=True,
            samesite="lax",
            max_age=DEFAULT_TOKEN_EXPIRE_HOURS * 3600
        )
    return login_result


def clear_auth_cookie(response: Response) -> None:
    """清除认证 cookie"""
    response.delete_cookie(key="auth_token")
