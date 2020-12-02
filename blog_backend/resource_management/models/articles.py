""" articles.py

    This defines how we store article's raw document, compiled document,
    and its edit history.
"""
from typing import final

from django.db import models
from .utils import BaseModel

__all__ = ["Article", "RawArticleData", "ArticleEditHistory", "CompiledArticleData"]


# Top level article instance.
# It has reference to CompiledArticleData in order to retrieve compiled HTML.
@final
class Article(BaseModel):
    synonym = models.SlugField(
        db_index=True, max_length=100, unique=True, null=False, blank=False
    )
    title = models.CharField(max_length=200, null=False, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


# Raw Markdown article data.
@final
class RawArticleData(BaseModel):
    article = models.OneToOneField(
        Article,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="raw_data",
        related_query_name="raw_article_data",
    )
    created = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=30, null=False, blank=False)
    last_update = models.DateTimeField(auto_now=True)
    data = models.TextField(null=False, blank=False)


# Unified document diff information for each update.
# If we really need to convert article back to historical version, then
# we'll be able to retrieve the edit history and further run rollback.
@final
class ArticleEditHistory(BaseModel):
    """
    Note: Recovery may be rarely used, so right now we're not adding other
    indices to this table.
    """

    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        related_name="edit_histories",
        related_query_name="article_edit_history",
    )
    created = models.DateTimeField(auto_now_add=True)
    # Modifications on Article instance
    previous_title = models.CharField(max_length=200, null=True)
    previous_synonym = models.SlugField(max_length=100, null=True)
    # Modifications on RawArticleData instance
    previous_version = models.CharField(max_length=30, null=True)
    #   Text diff info to n
    update_data = models.TextField(null=True)
    recover_data = models.TextField(null=True)


@final
class CompiledArticleData(BaseModel):
    article = models.OneToOneField(
        Article,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="compiled_data",
        related_query_name="compile_article_data",
    )
    last_update = models.DateTimeField(auto_now=True)
    data = models.TextField(null=False, blank=False)
