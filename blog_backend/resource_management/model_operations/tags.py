from typing import final, Iterable

from django.db.models.query import QuerySet

from resource_management.models import (
    Tag,
    ArticleTag,
    Article,
)
from resource_management.model_operations.utils import (
    BaseOperation,
    BaseBulkOperation,
)

__all__ = [
    "TagOperations",
    "ArticleTagOperations",
]


@final
class TagOperations(BaseOperation, BaseBulkOperation):
    base_model = Tag

    @classmethod
    def get_tag_by_name(cls, tag_name: str) -> Tag:
        return cls.base_model.objects.get(tag_name=tag_name)

    @classmethod
    def get_tags_from_article(cls, article: Article) -> QuerySet[Tag]:
        return cls.base_model.objects.filter(article_tag__article=article)

    @classmethod
    def get_tags_from_article_synonym(cls, synonym: str) -> QuerySet[Tag]:
        return cls.base_model.objects.filter(article_tag__article__synonym=synonym)

    @classmethod
    def get_all_tags(cls) -> Iterable[str]:
        return cls.base_model.objects.values_list("tag_name", flat=True).order_by(
            "tag_name"
        )


@final
class ArticleTagOperations(BaseOperation, BaseBulkOperation[ArticleTag]):
    base_model = ArticleTag

    @classmethod
    def get_tag_relations_from_article(
        cls, article: Article, prefetch_tags: bool = False
    ) -> QuerySet[ArticleTag]:
        query = cls.base_model.objects.filter(article=article)
        if prefetch_tags:
            query = query.select_related("tag")

        return query
