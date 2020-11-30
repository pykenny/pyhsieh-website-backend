from django.http import JsonResponse
from django.views.decorators.http import require_GET

from resource_management.service.blog_post import (
    get_posts_by_page,
    get_post_data,
    get_all_tags,
)

__all__ = [
    "posts_by_page",
    "posts_by_page_and_tag",
]


@require_GET
def posts_by_page(_, page):
    try:
        result = get_posts_by_page(page, 10)
    except:
        result = None
    return JsonResponse(result)


@require_GET
def posts_by_page_and_tag(_, page, tag):
    result = get_posts_by_page(page, 10, tag)
    return JsonResponse(result)


@require_GET
def get_article_data(_, article_synonym):
    result = get_post_data(article_synonym)
    return JsonResponse(result)


@require_GET
def get_tag_list(_):
    result = {"data": get_all_tags()}
    return JsonResponse(result)
