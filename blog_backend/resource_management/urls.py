from django.urls import path
import resource_management.views.blog_post as blog_post
import resource_management.views.images as images

urlpatterns = [
    path("posts_by_page/<int:page>", blog_post.posts_by_page),
    path("posts_by_page_and_tag/<int:page>/<str:tag>", blog_post.posts_by_page_and_tag),
    path("get_article_data/<str:synonym>", blog_post.get_article_data),
    path("get_tag_list/", blog_post.get_tag_list),
    path("get_full_file_path/<str:file_name>", images.get_full_file_path),
]
