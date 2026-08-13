from datetime import datetime

from src.model.system.user import ALL_MODULES, USER_ROLE_USER
from src.schema.common.base import SchemaModel


class AccountResource(SchemaModel):
    username: str
    created_at: datetime
    last_login_at: datetime | None = None
    role: str = USER_ROLE_USER
    permissions: list[str] | None = None


class AccountUpdateRequest(SchemaModel):
    username: str


class AccountPasswordChangeRequest(SchemaModel):
    current_password: str
    new_password: str


class AccountCreateRequest(SchemaModel):
    """管理员创建账号；role 默认为普通用户，permissions 缺省表示授予全部模块。"""

    username: str
    password: str
    role: str = USER_ROLE_USER
    permissions: list[str] | None = None


class AccountAdminUpdateRequest(SchemaModel):
    """管理员调整账号的角色与模块权限；字段均可选，仅更新提供的部分。"""

    role: str | None = None
    permissions: list[str] | None = None
