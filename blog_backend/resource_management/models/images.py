""" images.py

    This defines path to images and their meta information such as alias.

    Note: We're making it a soft-deletion model to keep track of previously used
          images.
"""
from uuid import uuid4
from typing import Final, final

from django.db import models
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE

from resource_management.models import Article

__all__ = ["Image"]

_FILENAME_FORMAT: Final = "{uuid_str:s}.{ext:s}"


@final
class Image(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        indexes = [
            models.Index(
                fields=["article", "alias"],
                name="idx_image_resolution_group",
            ),
            models.Index(
                fields=["article", "alias", "resolution"],
                name="idx_image_identity",
            ),
        ]

    class ImageResolutionType(models.IntegerChoices):
        # Note: Only use 'ORIGINAL' when you want to force it to be the
        #       only available size of the image.
        # General resolution scale by image width:
        #     LOW    --  320px  <<  Fallback for old browsers
        #     MEDIUM --  640px
        #     LARGE  --  960px
        #     HIGH   -- 1280px
        ORIGINAL = 1
        LOW = 2
        MEDIUM = 3
        LARGE = 4
        HIGH = 5

    uuid = models.UUIDField(primary_key=True, default=uuid4)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="images",
        related_query_name="image",
    )
    alias = models.CharField(max_length=100, null=False, blank=False)
    extension = models.CharField(max_length=10, null=False, blank=False)
    resolution = models.IntegerField(choices=ImageResolutionType.choices)
    height = models.PositiveIntegerField(null=True)
    width = models.PositiveIntegerField(null=True)

    @property
    def file_name(self) -> str:
        return _FILENAME_FORMAT.format(uuid_str=str(self.uuid), ext=self.extension)
