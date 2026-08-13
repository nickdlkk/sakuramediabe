from fastapi import APIRouter, Depends, Response, status

from src.api.routers.deps import (
    db_deps,
    get_current_user,
    require_admin_dependency,
    require_module_dependency,
)
from src.model.system.user import MODULE_MEDIA_LIBRARIES
from src.schema.playback.media_libraries import (
    MediaLibraryCreateRequest,
    MediaLibraryResource,
    MediaLibraryUpdateRequest,
)
from src.service.playback import MediaLibraryService

router = APIRouter(
    prefix="/media-libraries",
    tags=["media-libraries"],
    dependencies=[Depends(db_deps)],
)


@router.get(
    "",
    response_model=list[MediaLibraryResource],
    dependencies=[Depends(require_module_dependency(MODULE_MEDIA_LIBRARIES))],
)
def list_media_libraries(current_user=Depends(get_current_user)):
    return MediaLibraryService.list_libraries()


@router.post(
    "",
    response_model=MediaLibraryResource,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_dependency)],
)
def create_media_library(
    payload: MediaLibraryCreateRequest,
    current_user=Depends(get_current_user),
):
    return MediaLibraryService.create_library(payload)


@router.patch(
    "/{library_id}",
    response_model=MediaLibraryResource,
    dependencies=[Depends(require_admin_dependency)],
)
def update_media_library(
    library_id: int,
    payload: MediaLibraryUpdateRequest,
    current_user=Depends(get_current_user),
):
    return MediaLibraryService.update_library(library_id, payload)


@router.delete(
    "/{library_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin_dependency)],
)
def delete_media_library(library_id: int, current_user=Depends(get_current_user)):
    MediaLibraryService.delete_library(library_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
