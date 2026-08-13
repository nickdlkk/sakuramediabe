from __future__ import annotations

from peewee import ForeignKeyField

from playhouse.migrate import migrate as run_migration

from src.model.system.user import User
from src.start.migrations import SkipMigration

name = "20260813_02_add_refresh_token_user"


def migrate(database, migrator) -> None:
    """刷新令牌归属到具体用户，修复多用户下 refresh 取首个用户导致的串号问题。"""
    if not database.table_exists("user_refresh_tokens"):
        raise SkipMigration("user_refresh_tokens table does not exist")

    user_field = ForeignKeyField(User, null=True, index=True, on_delete="CASCADE")
    run_migration(migrator.add_column("user_refresh_tokens", "user", user_field))

    # 存量令牌归属到首个用户（既有唯一账号即管理员）。
    first_user = User.select().order_by(User.id).first()
    if first_user is not None:
        database.execute_sql(
            "UPDATE user_refresh_tokens SET user_id = %s WHERE user_id IS NULL",
            (first_user.id,),
        )
