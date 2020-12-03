from django.http import JsonResponse
from django.views.decorators.http import require_GET

import resource_management.service.blog_post as blog_post

from .utils import json_404_on_error
from .constants import PAGE_SIZE

__all__ = [
    "posts_by_page",
    "posts_by_page_and_tag",
    "get_post_data",
    "get_tag_list",
]


@require_GET
@json_404_on_error
def posts_by_page(_, page):
    result = blog_post.get_posts_by_page(page, PAGE_SIZE)

    return JsonResponse(result)


@require_GET
@json_404_on_error
def posts_by_page_and_tag(_, tag, page):
    result = blog_post.get_posts_by_page(page, PAGE_SIZE, tag)

    return JsonResponse(result)


@require_GET
@json_404_on_error
def get_post_data(_, synonym):
    result = blog_post.get_post_data(synonym)
    return JsonResponse(result)


@require_GET
@json_404_on_error
def get_tag_list(_):
    result = {"data": blog_post.get_all_tags()}
    return JsonResponse(result)
