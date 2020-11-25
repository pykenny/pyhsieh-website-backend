from os.path import splitext
from typing import final, Iterable, Optional

from django.core.exceptions import ObjectDoesNotExist

from safedelete.queryset import SafeDeleteQueryset

from resource_management.models import (
    Article,
    Image,
)
from resource_management.model_operations.utils import (
    BaseOperation,
    BaseBulkOperation,
)

__all__ = [
    "ImageOperations",
]


@final
class ImageOperations(BaseOperation, BaseBulkOperation[Image]):
    base_model = Image

    # These methods will pull out all available image data, and exclude
    # original file by default.
    @classmethod
    def get_images_by_article(
        cls, article: Article, include_original: bool = False
    ) -> SafeDeleteQueryset[Image]:
        query = cls.base_model.objects.filter(article=article)
        if not include_original:
            query = query.exclude(resolution=Image.ImageResolutionType.ORIGINAL)
        return query

    @classmethod
    def get_images_by_article_synonym(
        cls, synonym: str, include_original: bool = False
    ) -> SafeDeleteQueryset[Image]:
        query = cls.base_model.objects.filter(article__synonym=synonym)
        if not include_original:
            query = query.exclude(resolution=Image.ImageResolutionType.ORIGINAL)
        return query

    # Methods for obtaining full image list (represented by original resolution)
    @classmethod
    def get_original_images(cls, article: Article) -> SafeDeleteQueryset[Image]:
        return cls.base_model.objects.filter(
            article=article,
            resolution=Image.ImageResolutionType.ORIGINAL,
        )

    @classmethod
    def get_original_images_by_article_synonym(
        cls, article_synonym: str
    ) -> SafeDeleteQueryset[Image]:
        return cls.base_model.objects.filter(
            article__synonym=article_synonym,
            resolution=Image.ImageResolutionType.ORIGINAL,
        )

    # Methods for obtaining image data with specified aliases
    @classmethod
    def get_images_by_article_and_aliases(
        cls, article: Article, aliases: Iterable[str], include_original: bool = False
    ) -> SafeDeleteQueryset[Image]:
        query = cls.base_model.objects.filter(article=article, alias__in=aliases)
        if not include_original:
            query.exclude(resolution=Image.ImageResolutionType.ORIGINAL)

        return query

    @classmethod
    def get_images_by_article_synonym_and_aliases(
        cls,
        article_synonym: str,
        aliases: Iterable[str],
        include_original: bool = False,
    ) -> SafeDeleteQueryset[Image]:
        query = cls.base_model.objects.filter(
            article__synonym=article_synonym, alias__in=aliases
        )
        if not include_original:
            query.exclude(resolution=Image.ImageResolutionType.ORIGINAL)

        return query

    @classmethod
    def get_image_by_file_name(cls, file_name: str) -> Optional[Image]:
        """ Return the object, or None if it doesn't exist in DB """
        uuid_str, ext = splitext(file_name)
        try:
            return cls.base_model.objects.filter(uuid=uuid_str, extension=ext).get()
        except ObjectDoesNotExist:
            return None
