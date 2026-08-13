from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.api.exception.errors import ApiError
from src.common.database import ensure_database_ready
from src.model import User
from src.service.system.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/docs-token", auto_error=False)


def db_deps():
    return ensure_database_ready()


def get_current_user(
    access_token: str | None = Depends(oauth2_scheme),
):
    if access_token is None:
        raise ApiError(401, "unauthorized", "Authentication required")
    return AuthService.get_current_user(access_token)


def require_admin_dependency(user: User = Depends(get_current_user)) -> User:
    """FastAPI 依赖：当前用户必须是管理员，否则抛出 403。"""
    AuthService.require_admin(user)
    return user


def require_module_dependency(module: str):
    """工厂：返回一个 FastAPI 依赖，校验当前用户拥有指定功能模块，否则抛出 403。

    管理员隐式拥有全部模块，因此恒通过。
    """

    def _dependency(user: User = Depends(get_current_user)) -> User:
        AuthService.require_module(user, module)
        return user

    return _dependency
