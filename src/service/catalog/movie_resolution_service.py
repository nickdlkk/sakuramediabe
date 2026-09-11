"""影片最高分辨率档位查询。"""

from peewee import fn

from src.api.exception.errors import ApiError
from src.model import Media, Movie

RESOLUTION_LEVELS = (
    ("8K", 4320),
    ("4K", 2160),
    ("2K", 1440),
    ("1080P", 1080),
    ("720P", 720),
    ("480P", 480),
    ("360P", 360),
)



def resolution_height_expression():
    """解析 ``WxH`` 分辨率的 height 分量（probe 写入形态），供阈值比较与分桶复用。"""
    return fn.split_part(Media.resolution, "x", 2).cast("int")


def resolution_interval(resolution: str | None, *, error_code: str = "invalid_playlist_filter") -> tuple[int | None, int | None]:
    """解析分辨率筛选档位为 ``[threshold, upper)`` 高度区间；非法档位抛 422。

    档位互斥：4K 命中 ``[2160, 4320)``，8K 命中 ``[4320, ...)``，8K 影片不会误入 4K。
    """
    if resolution is None:
        return (None, None)
    normalized = resolution.strip().lower()
    for index, (label, threshold) in enumerate(RESOLUTION_LEVELS):
        if label.lower() == normalized:
            upper = RESOLUTION_LEVELS[index - 1][1] if index > 0 else None
            return (threshold, upper)
    raise ApiError(
        422,
        error_code,
        "Invalid resolution filter",
        {"resolution": resolution},
    )


def resolution_exists_expression(resolution: str, *, error_code: str = "invalid_playlist_filter"):
    """构造「影片最高分辨率落在档位区间」的 EXISTS 子查询。

    对 media 分组后按 MAX(height) 归入精确档位，只匹配 ``WxH`` 形态（probe 写入），
    无法解析的脏值直接排除。
    """
    threshold, upper = resolution_interval(resolution, error_code=error_code)
    height_expression = resolution_height_expression()
    having_conditions = [fn.MAX(height_expression) >= threshold]
    if upper is not None:
        having_conditions.append(fn.MAX(height_expression) < upper)
    return fn.EXISTS(
        Media.select(fn.COUNT(Media.id))
        .where(
            Media.movie == Movie.movie_number,
            Media.valid == True,
            Media.resolution.regexp(r"^\d+x\d+$"),
        )
        .group_by(Media.movie)
        .having(*having_conditions)
    )
