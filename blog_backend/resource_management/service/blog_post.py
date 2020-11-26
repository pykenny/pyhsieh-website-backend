from typing import List, Dict, Optional, Any

from resource_management.model_operations import (
    ArticleOperations,
    CompiledArticleDataOperations,
    TagOperations,
)

# TODOs: Should I "ring the bell" in view functions?

__all__ = [
    "get_posts_by_page",
    "get_post_data",
    "get_all_tags",
]


def get_posts_by_page(page: int, tag: Optional[str] = None) -> Dict[str, Any]:
    """Provide title, alias, time, and tags. Ordered by time in desc order.
    Also, points out whether the previous or next page exists.
    """
    search_result = ArticleOperations.get_article_page_list(page, tag=tag)
    # Stupid serialization
    posts = [
        {
            "title": article_entry.title,
            "synonym": article_entry.synonym,
            "created": article_entry.created.strftime("%Y%m%d-%H%m%S"),
            "tags": [
                tag_entry.tag_name
                for tag_entry in TagOperations.get_tags_from_article(article_entry)
            ],
        }
        for article_entry in search_result.article_list
    ]

    return {
        "has_next_page": search_result.has_next_page,
        "has_prev_page": search_result.has_prev_page,
        "posts": posts,
    }


def get_post_data(synonym: str) -> Dict[str, Any]:
    """ Provide post title, XML based on article alias """
    post_entry = ArticleOperations.get_article_by_synonym(synonym, prefetch_for_blog=True)
    prev_post, next_post = ArticleOperations.get_prev_and_next_article(post_entry.id)
    raw_xml = CompiledArticleDataOperations.get_compiled_data(post_entry).data
    return {
        "title": post_entry.title,
        "created": post_entry.created.strftime("%Y%m%d-%H%m%S"),
        "content": raw_xml,
        "tags": [
            tag_entry.tag_name
            for tag_entry in TagOperations.get_tags_from_article(post_entry)
        ],
        "synonym_prev": prev_post.synonym,
        "synonym_next": next_post.synonym,
    }


def get_all_tags() -> List[str]:
    return list(TagOperations.get_all_tags())
