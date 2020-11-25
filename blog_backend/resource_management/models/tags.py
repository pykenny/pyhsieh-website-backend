""" tags.py

    This defines how we store tag information and relationship with articles
"""
from typing import final

from django.db import models
from .utils import BaseModel

from resource_management.models import Article

__all__ = [
    "Tag",
    "ArticleTag",
]


# Tag information.
# Create date is not important so we skip timestamp creation here.
@final
class Tag(BaseModel):
    tag_name = models.CharField(unique=True, max_length=50, null=False, blank=False)


# Intermediate table for many-to-many relationship
@final
class ArticleTag(BaseModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["article", "tag"], name="identity"),
        ]

    created = models.DateTimeField(auto_now_add=True)
    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        related_name="tags_of_article",
        related_query_name="article_tag",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.PROTECT,
        related_name="articles_of_tag",
        related_query_name="article_tag",
    )
