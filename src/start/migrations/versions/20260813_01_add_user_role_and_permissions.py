from __future__ import annotations

import json

from peewee import CharField
from playhouse.migrate import migrate as run_migration

from src.model.base import JsonTextField
from src.model.system.user import ALL_MODULES, USER_ROLE_ADMIN
from src.start.migrations import SkipMigration

name = "20260813_01_add_user_role_and_permissions"


def migrate(database, migrator) -> None:
    """为用户表补充角色与权限字段，支撑多账号权限体系。

    - role：存量用户统一置为管理员，保持「首个/唯一账号即管理员」的既有语义。
    - permissions：JSON 文本列，存放启用模块标识列表；存量管理员回填为全量模块。
    """
    if not database.table_exists("users"):
        raise SkipMigration("users table does not exist")

    role_field = CharField(default=USER_ROLE_ADMIN, null=False)
    run_migration(migrator.add_column("users", "role", role_field))

    permissions_field = JsonTextField(null=True)
    run_migration(migrator.add_column("users", "permissions", permissions_field))

    # 存量管理员权限回填为全量模块（新建迁移前的唯一账号即管理员）。
    permissions_json = json.dumps(list(ALL_MODULES), ensure_ascii=False)
    database.execute_sql(
        "UPDATE users SET permissions = %s "
        "WHERE role = %s AND permissions IS NULL",
        (permissions_json, USER_ROLE_ADMIN),
    )
