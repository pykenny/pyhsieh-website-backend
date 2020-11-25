from resource_management.model_operations.images import ImageOperations
from resource_management.utils.images import get_image_full_path

__all__ = [
    "get_full_file_path",
]


def get_full_file_path(filename: str) -> dict:
    image_entry = ImageOperations.get_image_by_file_name(filename)
    if not image_entry:
        # TODO: Ring the bell!
        pass
    else:
        return {"path": get_image_full_path(image_entry)}
