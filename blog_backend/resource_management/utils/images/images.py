import stat
from os import chmod
from shutil import chown
from os.path import join as path_join
from PIL import (
    Image as PILImage,
    ImageFile,
)
from collections import OrderedDict as OrderedDictCls
from typing import Final, final, IO, Optional, OrderedDict

from django.conf import settings
from resource_management.models.images import Image


# Allow loading truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

__all__ = [
    "resize_image",
    "image_compare",
    "get_image_full_path",
    "save_image",
    "ImgSrcNotProvidedError",
]

_RESOLUTION_WIDTH_MAPPING: Final = (
    (Image.ImageResolutionType.LOW, 320),
    (Image.ImageResolutionType.MEDIUM, 640),
    (Image.ImageResolutionType.LARGE, 960),
    (Image.ImageResolutionType.HIGH, 1280),
)

_BUF_SIZE: Final = 8 * 1024


@final
class ImgSrcNotProvidedError(Exception):
    DEFAULT_MESSAGE = "A PIL.Image or readable IO instance should be provided."

    def __init__(self, message: str = DEFAULT_MESSAGE):
        super().__init__(message)


def resize_image(
    fp: IO[bytes],
) -> OrderedDict[Image.ImageResolutionType, PILImage.Image]:
    """Resize image as much as it can and return mapping between
    resolution Enum and processed image.

    If the input image is smaller than least width requirement on
    the list, then a copy of the same image will be provided to the
    lowest resolution.
    """
    result = OrderedDictCls()

    with PILImage.open(fp) as im:
        width, height = im.size
        # We still need size information when filling up DB entries, so
        # here we create a clone of original buffer
        result[Image.ImageResolutionType.ORIGINAL] = im.copy()
        for enum_val, c_width in _RESOLUTION_WIDTH_MAPPING:
            # If can't further compressed for higher resolution, then exit;
            # if it's even smaller than LOW's requirement, then take a clone
            # for the lowest quality.
            if c_width > width:
                if enum_val == Image.ImageResolutionType.LOW:
                    result[enum_val] = im.copy()
                break
            else:
                c_height = int(height * (c_width / width))
                result[enum_val] = im.resize((c_width, c_height), PILImage.LANCZOS)

    return result


def image_compare(stream_a: IO[bytes], path_b: str) -> bool:
    # Given binary stream reader stream_a, compare its content
    # with file stored in path_b.

    # We're not using filecmp here because it assumes the two
    # input are both file path.
    # Algorithm Reference: https://codereview.stackexchange.com/a/171014
    with open(path_b, "rb") as stream_b:
        while True:
            buffer_a = stream_a.read(_BUF_SIZE)
            buffer_b = stream_b.read(_BUF_SIZE)
            if buffer_a != buffer_b:
                return False
            if not buffer_a:
                return True


def get_image_full_path(entry: Image) -> str:
    if entry.resolution == Image.ImageResolutionType.ORIGINAL:
        return path_join(settings.PROTECTED_IMAGE_DIR, entry.file_name)
    return path_join(settings.OPENED_IMAGE_DIR, entry.file_name)


def save_image(
    entry: Image,
    img_buffer: Optional[PILImage.Image] = None,
    img_stream: Optional[IO[bytes]] = None,
) -> None:
    target_path = get_image_full_path(entry)
    target_group: str = (
        settings.OPENED_IMAGE_GROUP
        if entry.resolution == Image.ImageResolutionType.ORIGINAL
        else settings.PROTECTED_IMAGE_GROUP
    )
    if img_buffer:
        img_buffer.save(target_path)
    elif img_stream:
        with open(target_path, "wb") as fd_w:
            fd_w.write(img_stream.read())
    else:
        raise ImgSrcNotProvidedError()

    # Note: Share with OPENED_GROUP to let frontend server access
    # these images. Otherwise, mask it to make it available to backend
    # server only.
    chown(target_path, group=target_group)
    # Note: Only backend server's runner can modify image files.
    chmod(target_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
