from fastapi import APIRouter, Depends, Response, status

from src.api.routers.deps import db_deps, get_current_user
from src.schema.system.account import (
    AccountAdminUpdateRequest,
    AccountCreateRequest,
    AccountResource,
)
from src.service.system.account_service import AccountService

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(db_deps)],
)


@router.get("", response_model=list[AccountResource])
def list_accounts(current_user=Depends(get_current_user)):
    """列出全部账号（仅管理员）。"""
    return AccountService.list_accounts(current_user)


@router.post(
    "",
    response_model=AccountResource,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    payload: AccountCreateRequest,
    current_user=Depends(get_current_user),
):
    """创建账号并指定角色与功能模块权限（仅管理员）。"""
    return AccountService.create_account(current_user, payload)


@router.get("/{username}", response_model=AccountResource)
def get_account(username: str, current_user=Depends(get_current_user)):
    """查看单个账号（仅管理员）。"""
    return AccountService.get_account_by_username(current_user, username)


@router.patch("/{username}", response_model=AccountResource)
def update_account(
    username: str,
    payload: AccountAdminUpdateRequest,
    current_user=Depends(get_current_user),
):
    """调整账号角色与模块权限（仅管理员）。"""
    return AccountService.update_account_admin(current_user, username, payload)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(username: str, current_user=Depends(get_current_user)):
    """删除账号（仅管理员，不可删除自身）。"""
    AccountService.delete_account(current_user, username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
