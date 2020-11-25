from django.http import JsonResponse

from resource_management.service.blog_post import (
    get_posts_by_page,
    get_post_data,
    get_all_tags,
)

__all__ = [
    "posts_by_page",
    "posts_by_page_and_tag",
]


def posts_by_page(page):
    result = get_posts_by_page(page)
    return JsonResponse(result)


def posts_by_page_and_tag(page, tag):
    result = get_posts_by_page(page, tag)
    return JsonResponse(result)


def get_article_data(article_synonym):
    result = get_post_data(article_synonym)
    return JsonResponse(result)


def get_tag_list():
    result = {"data": get_all_tags()}
    return JsonResponse(result)
