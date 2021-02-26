from django.core.exceptions import ObjectDoesNotExist

from resource_management.models import Image
from resource_management.model_operations.images import ImageOperations
from resource_management.utils.images import get_image_full_path

__all__ = [
    "get_full_file_path",
]


def get_full_file_path(filename: str) -> dict:
    image_entry = ImageOperations.get_image_by_file_name(filename)
    if image_entry.resolution == Image.ImageResolutionType.ORIGINAL:
        raise ObjectDoesNotExist()

    return {"data": get_image_full_path(image_entry)}
