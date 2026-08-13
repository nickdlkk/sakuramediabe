import bcrypt

from src.api.exception.errors import ApiError
from src.model import User, UserRefreshToken
from src.model.system.user import ALL_MODULES, USER_ROLE_ADMIN, USER_ROLE_USER
from src.schema.system.account import (
    AccountAdminUpdateRequest,
    AccountCreateRequest,
    AccountResource,
    AccountUpdateRequest,
)
from src.service.system.auth_service import AuthService


class AccountService:
    @staticmethod
    def get_account(user: User) -> AccountResource:
        return AccountResource.from_attributes_model(user)

    @staticmethod
    def update_account(user: User, payload: AccountUpdateRequest) -> AccountResource:
        update_data = payload.model_dump(exclude_unset=True, by_alias=False)
        username = update_data["username"]
        existing_user = User.get_or_none(User.username == username)
        if existing_user is not None and existing_user.id != user.id:
            raise ApiError(409, "username_conflict", "Username already exists")

        for field_name, value in update_data.items():
            setattr(user, field_name, value)
        user.save()
        return AccountService.get_account(user)

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> None:
        if not bcrypt.checkpw(
            current_password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            raise ApiError(401, "invalid_credentials", "Current password is incorrect")

        user.password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        user.save()
        UserRefreshToken.delete().execute()

    # ----- 管理员视角：账号与权限管理 -----

    @staticmethod
    def list_accounts(requester: User) -> list[AccountResource]:
        AuthService.require_admin(requester)
        users = User.select().order_by(User.username)
        return AccountResource.from_items(users)

    @staticmethod
    def create_account(
        requester: User, payload: AccountCreateRequest
    ) -> AccountResource:
        AuthService.require_admin(requester)
        username = (payload.username or "").strip()
        if not username:
            raise ApiError(400, "invalid_username", "Username is required")

        if User.get_or_none(User.username == username) is not None:
            raise ApiError(409, "username_conflict", "Username already exists")

        if payload.role not in (USER_ROLE_ADMIN, USER_ROLE_USER):
            raise ApiError(400, "invalid_role", "Role must be 'admin' or 'user'")

        # permissions 缺省授予全部模块；显式传入时校验只能取自有模块集合。
        permissions = payload.permissions
        if permissions is None:
            permissions = list(ALL_MODULES)
        invalid_modules = [module for module in permissions if module not in ALL_MODULES]
        if invalid_modules:
            raise ApiError(
                400,
                "invalid_module",
                f"Unknown module(s): {invalid_modules}",
            )

        password_hash = bcrypt.hashpw(
            payload.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        user = User.create(
            username=username,
            password_hash=password_hash,
            role=payload.role,
            permissions=permissions,
        )
        return AccountResource.from_attributes_model(user)

    @staticmethod
    def get_account_by_username(requester: User, username: str) -> AccountResource:
        AuthService.require_admin(requester)
        user = User.get_or_none(User.username == username)
        if user is None:
            raise ApiError(404, "account_not_found", "Account not found")
        return AccountResource.from_attributes_model(user)

    @staticmethod
    def update_account_admin(
        requester: User,
        username: str,
        payload: AccountAdminUpdateRequest,
    ) -> AccountResource:
        AuthService.require_admin(requester)
        user = User.get_or_none(User.username == username)
        if user is None:
            raise ApiError(404, "account_not_found", "Account not found")

        if payload.role is not None:
            if payload.role not in (USER_ROLE_ADMIN, USER_ROLE_USER):
                raise ApiError(400, "invalid_role", "Role must be 'admin' or 'user'")
            user.role = payload.role

        if payload.permissions is not None:
            invalid_modules = [
                module for module in payload.permissions if module not in ALL_MODULES
            ]
            if invalid_modules:
                raise ApiError(
                    400,
                    "invalid_module",
                    f"Unknown module(s): {invalid_modules}",
                )
            user.permissions = payload.permissions

        user.save()
        return AccountResource.from_attributes_model(user)

    @staticmethod
    def delete_account(requester: User, username: str) -> None:
        AuthService.require_admin(requester)
        user = User.get_or_none(User.username == username)
        if user is None:
            raise ApiError(404, "account_not_found", "Account not found")
        if user.id == requester.id:
            raise ApiError(
                400, "cannot_delete_self", "You cannot delete your own account"
            )
        user.delete_instance()
