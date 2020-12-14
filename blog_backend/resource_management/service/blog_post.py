from typing import Final, List, Dict, Optional, Any

from resource_management.model_operations import (
    ArticleOperations,
    CompiledArticleDataOperations,
    TagOperations,
)

__all__ = [
    "get_posts_by_page",
    "get_post_data",
    "get_all_tags",
]

DATE_FORMAT: Final = "%Y%m%d-%H%m%S"


def get_posts_by_page(
    page: int, page_size: int, tag: Optional[str] = None
) -> Dict[str, Any]:
    """Provide title, alias, time, and tags. Ordered by time in desc order.
    Also, points out whether the previous or next page exists.
    """
    search_result = ArticleOperations.get_article_page_list(
        page, page_size, tag=tag, prefetch_for_blog=True
    )
    posts = [
        {
            "title": article_entry.title,
            "synonym": article_entry.synonym,
            "timestamp": article_entry.created.strftime(DATE_FORMAT),
            "tags": [
                tag_entry.tag_name
                for tag_entry in TagOperations.get_tags_from_article(article_entry)
            ],
        }
        for article_entry in search_result.article_list
    ]

    return {
        "page_num": page,
        "tag": tag,
        "has_next_page": search_result.has_next_page,
        "has_prev_page": search_result.has_prev_page,
        "posts": posts,
    }


def get_post_data(synonym: str) -> Dict[str, Any]:
    """ Provide post title, XML based on article alias """
    post_entry = ArticleOperations.get_article_by_synonym(
        synonym, prefetch_for_blog=True
    )
    prev_post, next_post = ArticleOperations.get_prev_and_next_article_synonyms(
        post_entry
    )
    raw_xml = CompiledArticleDataOperations.get_compiled_data(post_entry).data
    return {
        "title": post_entry.title,
        "timestamp": post_entry.created.strftime(DATE_FORMAT),
        "content": raw_xml,
        "tags": [
            tag_entry.tag_name
            for tag_entry in TagOperations.get_tags_from_article(post_entry)
        ],
        "synonym_prev": prev_post,
        "synonym_next": next_post,
    }


def get_all_tags() -> List[str]:
    return list(TagOperations.get_all_tags())
