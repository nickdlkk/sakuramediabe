from peewee import CharField, DateTimeField

from src.model.base import BaseModel, JsonTextField
from src.model.mixins import TimestampedMixin

# 角色：管理员可管理账号与权限；普通用户仅按自身 permissions 使用各功能模块。
USER_ROLE_ADMIN = "admin"
USER_ROLE_USER = "user"
USER_ROLES = (USER_ROLE_ADMIN, USER_ROLE_USER)

# 功能模块标识，与前端 AppModulePermission 的 wireValue 对齐（name 即 wire 值）。
MODULE_SEARCH = "search"
MODULE_MEDIA_LIBRARIES = "mediaLibraries"
MODULE_DOWNLOAD_MANAGEMENT = "downloadManagement"

ALL_MODULES: tuple[str, ...] = (
    MODULE_SEARCH,
    MODULE_MEDIA_LIBRARIES,
    MODULE_DOWNLOAD_MANAGEMENT,
)


class User(TimestampedMixin, BaseModel):
    username = CharField(unique=True, index=True)
    password_hash = CharField()
    last_login_at = DateTimeField(null=True)
    role = CharField(default=USER_ROLE_USER, null=False)
    # 启用（可见/可用）的功能模块标识列表；null 表示无（普通用户默认空权限）。
    permissions = JsonTextField(null=True)

    class Meta:
        table_name = "users"

    @property
    def is_admin(self) -> bool:
        return self.role == USER_ROLE_ADMIN

    def has_module(self, module: str) -> bool:
        """当前用户是否拥有指定功能模块。

        管理员默认拥有全部模块；普通用户仅当模块显式出现在 permissions 中才拥有。
        """
        if self.is_admin:
            return True
        enabled = self.permissions
        if not enabled:
            return False
        return module in enabled
