from typing import NamedTuple, Tuple, Optional, final

from django.db.models.query import QuerySet

from resource_management.models import (
    Article,
    RawArticleData,
    ArticleEditHistory,
    CompiledArticleData,
)
from resource_management.model_operations.utils import BaseOperation

__all__ = [
    "ArticlePageListResult",
    "ArticleOperations",
    "RawArticleDataOperations",
    "ArticleEditHistoryOperations",
    "CompiledArticleDataOperations",
]


@final
class ArticlePageListResult(NamedTuple):
    article_list: QuerySet[Article]
    has_next_page: bool
    has_prev_page: bool


@final
class ArticleOperations(BaseOperation):
    base_model = Article

    @classmethod
    def get_article_by_synonym(
        cls,
        article_synonym: str,
        prefetch_for_blog: bool = False,
    ) -> Article:
        query = cls.base_model.objects

        if prefetch_for_blog:
            query = query.select_related("compile_article_data").prefetch_related(
                "tags_of_article__tag",
            )

        return query.get(synonym=article_synonym)

    @classmethod
    def get_prev_and_next_article_synonyms(
        cls, article: Article
    ) -> Tuple[Optional[Article], Optional[Article]]:
        prev_post = (
            cls.base_model.objects.filter(id__lt=article.id).order_by("-id").values_list("synonym", flat=True).first()
        )
        next_post = (
            cls.base_model.objects.filter(id__gt=article.id).order_by("id").values_list("synonym", flat=True).first()
        )

        return prev_post, next_post

    @classmethod
    def get_article_page_list(
        cls, page: int, page_size: int = 10, tag: Optional[str] = None,
        prefetch_for_blog: bool = False,
    ) -> ArticlePageListResult:
        """ It's strongly suggested to apply offset for this function. """
        if (not isinstance(page, int)) or page <= 0:
            raise ValueError('"page" can not be float or non-positive integer.')
        if (not isinstance(page_size, int)) or page_size <= 0:
            raise ValueError('"page_size" can not be float or non-positive integer.')
        has_next_page = page != 1
        offset = (page - 1) * page_size
        article_list = cls.base_model.objects
        if tag:
            article_list = article_list.filter(tags_of_article__tag_name=tag)
        if prefetch_for_blog:
            article_list = article_list.prefetch_related("tags_of_article__tag")
        article_list = article_list.order_by("-id")[offset: (offset + page_size + 1)]
        has_prev_page = len(article_list) == page_size + 1

        return ArticlePageListResult(
            article_list=article_list,
            has_prev_page=has_prev_page,
            has_next_page=has_next_page,
        )


@final
class RawArticleDataOperations(BaseOperation):
    base_model = RawArticleData

    @classmethod
    def get_raw_data(cls, article: Article) -> RawArticleData:
        return cls.base_model.objects.get(article=article)

    @classmethod
    def get_raw_data_by_synonym(cls, synonym: str) -> RawArticleData:
        return cls.base_model.objects.get(article__synonym=synonym)


@final
class ArticleEditHistoryOperations(BaseOperation):
    base_model = ArticleEditHistory

    @classmethod
    def get_edit_histories(cls, article: Article) -> QuerySet[ArticleEditHistory]:
        return cls.base_model.objects.filter(article=article)

    @classmethod
    def get_edit_histories_by_synonym(cls, synonym: str) -> QuerySet[ArticleEditHistory]:
        return cls.base_model.objects.filter(article=synonym)


@final
class CompiledArticleDataOperations(BaseOperation):
    base_model = CompiledArticleData

    @classmethod
    def get_compiled_data(cls, article: Article) -> CompiledArticleData:
        return cls.base_model.objects.get(article=article)

    @classmethod
    def get_compiled_data_by_synonym(cls, synonym: str) -> CompiledArticleData:
        return cls.base_model.objects.get(article__synonym=synonym)
