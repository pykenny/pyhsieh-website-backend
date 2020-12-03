from os.path import join as path_join
from random import sample
from typing import NamedTuple

from django.test import TestCase
from django.utils.encoding import force_str

from jsonschema import validate

from resource_management.models import (
    Article,
    RawArticleData,
    CompiledArticleData,
    ArticleTag,
    Tag,
)
from resource_management.views.constants import (
    RESOURCE_NOT_FOUND_STATUS_CODE,
    RESOURCE_NOT_FOUND_JSON_DATA,
    SUCCESS_CODE,
    PAGE_SIZE,
)
from resource_management.tests.test_utils import TEST_FILE_ROOT_DIR
from .constants import (
    SCHEMA_POSTS_BY_PAGE,
    SCHEMA_POSTS_BY_PAGE_AND_TAG,
    SCHEMA_GET_POST_DATA,
    SCHEMA_GET_TAG_LIST,
    DATETIME_STR_FORMAT,
)


class ViewBlogPostTestCase(TestCase):
    class BlogPostData(NamedTuple):
        article: Article
        raw_data: RawArticleData
        compiled_data: CompiledArticleData

    @classmethod
    def setUpTestData(cls):
        raw_path = path_join(TEST_FILE_ROOT_DIR, "TestData_Raw/raw_document.md")
        compiled_path = path_join(
            TEST_FILE_ROOT_DIR, "TestData_Raw/compiled_document.xml"
        )
        cls.article_list = []
        cls.tags = ["zebra", "tag1", "tag2", "tag3"]
        cls.sorted_tags_full = sorted(cls.tags)
        cls.sorted_tags_partial = sorted(cls.tags[:-1])
        cls.num_articles = 201
        cls.num_tag3_posts = 51
        cls.tag3_article_ids = set(
            sample(range(1, cls.num_articles + 1), cls.num_tag3_posts)
        )
        cls.tag3_article_indices = sorted(
            (article_id - 1) for article_id in cls.tag3_article_ids
        )
        cls.tag_entries = []

        for tag_name in cls.tags:
            cls.tag_entries.append(Tag.objects.create(tag_name=tag_name))

        for article_id in range(1, cls.num_articles + 1):
            article = Article.objects.create(
                synonym="test-article-{0:d}".format(article_id),
                title="Test Article {0:d}".format(article_id),
            )
            raw_data = RawArticleData.objects.create(
                article=article,
                version="0.0.1",
                data=open(raw_path, "r").read(),
            )
            compiled_data = CompiledArticleData.objects.create(
                article=article,
                data=open(compiled_path, "r").read(),
            )

            for tag_entry in cls.tag_entries:
                if tag_entry.tag_name != "tag3" or article_id in cls.tag3_article_ids:
                    ArticleTag.objects.create(article=article, tag=tag_entry)

            cls.article_list.append(
                cls.BlogPostData(
                    article=article,
                    raw_data=raw_data,
                    compiled_data=compiled_data,
                )
            )

    def _call_posts_by_page_with_valid_args(self, page_num):
        negated_start_idx = -PAGE_SIZE * (page_num - 1) - 1
        negated_end_idx = -PAGE_SIZE * page_num - 1
        articles_data = self.article_list[negated_start_idx:negated_end_idx:-1]
        has_tag_3_list = [
            (self.num_articles + neg_idx + 1) in self.tag3_article_ids
            for neg_idx in range(negated_start_idx, negated_end_idx, -1)
        ]
        posts_data = [
            {
                "title": article_data.article.title,
                "synonym": article_data.article.synonym,
                "created": article_data.article.created.strftime(DATETIME_STR_FORMAT),
                "tags": self.sorted_tags_full
                if has_tag_3
                else self.sorted_tags_partial,
            }
            for has_tag_3, article_data in zip(has_tag_3_list, articles_data)
        ]
        response = self.client.get("/resource/posts_by_page/{0:d}".format(page_num))
        return posts_data, response

    def test_posts_by_page_first_page(self):
        page_num = 1
        posts_data, response = self._call_posts_by_page_with_valid_args(page_num)
        expected = {
            "page_num": page_num,
            "tag": None,
            "has_next_page": False,
            "has_prev_page": True,
            "posts": posts_data,
        }
        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_POSTS_BY_PAGE)
        self.assertDictEqual(response_json, expected)

    def test_posts_by_page_mid_page(self):
        page_num = 12
        posts_data, response = self._call_posts_by_page_with_valid_args(page_num)
        expected = {
            "page_num": page_num,
            "tag": None,
            "has_next_page": True,
            "has_prev_page": True,
            "posts": posts_data,
        }
        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_POSTS_BY_PAGE)
        self.assertDictEqual(response_json, expected)

    def test_posts_by_page_end(self):
        page_num = 21
        posts_data, response = self._call_posts_by_page_with_valid_args(page_num)
        expected = {
            "page_num": page_num,
            "tag": None,
            "has_next_page": True,
            "has_prev_page": False,
            "posts": posts_data,
        }
        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_POSTS_BY_PAGE)
        self.assertDictEqual(response_json, expected)

    def test_posts_by_page_out_of_range(self):
        invalid_page_nums = (0, 100)
        for page_num in invalid_page_nums:
            response = self.client.get("/resource/posts_by_page/{0:d}".format(page_num))
            self.assertEqual(response.status_code, RESOURCE_NOT_FOUND_STATUS_CODE)
            self.assertJSONEqual(
                force_str(response.content), RESOURCE_NOT_FOUND_JSON_DATA
            )

    def _call_posts_by_page_and_tag_with_valid_args(self, page_num, tag_name):
        articles_data = (
            self.article_list[idx]
            for idx in self.tag3_article_indices[
                -PAGE_SIZE * (page_num - 1) - 1 : -PAGE_SIZE * page_num - 1 : -1
            ]
        )
        posts_data = [
            {
                "title": article_data.article.title,
                "synonym": article_data.article.synonym,
                "created": article_data.article.created.strftime(DATETIME_STR_FORMAT),
                "tags": self.sorted_tags_full,
            }
            for article_data in articles_data
        ]
        response = self.client.get(
            "/resource/posts_by_page_and_tag/{0:s}/{1:d}".format(tag_name, page_num)
        )

        return posts_data, response

    def test_posts_by_page_and_tag_first(self):
        page_num = 1
        tag_name = "tag3"
        posts_data, response = self._call_posts_by_page_and_tag_with_valid_args(
            page_num, tag_name
        )
        expected = {
            "page_num": page_num,
            "tag": tag_name,
            "has_next_page": False,
            "has_prev_page": True,
            "posts": posts_data,
        }

        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_POSTS_BY_PAGE_AND_TAG)
        self.assertDictEqual(response_json, expected)

    def test_posts_by_page_and_tag_mid(self):
        page_num = 3
        tag_name = "tag3"
        posts_data, response = self._call_posts_by_page_and_tag_with_valid_args(
            page_num, tag_name
        )
        expected = {
            "page_num": page_num,
            "tag": tag_name,
            "has_next_page": True,
            "has_prev_page": True,
            "posts": posts_data,
        }

        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_POSTS_BY_PAGE_AND_TAG)
        self.assertDictEqual(response_json, expected)

    def test_posts_by_page_and_tag_last(self):
        page_num = 6
        tag_name = "tag3"
        posts_data, response = self._call_posts_by_page_and_tag_with_valid_args(
            page_num, tag_name
        )
        expected = {
            "page_num": page_num,
            "tag": tag_name,
            "has_next_page": True,
            "has_prev_page": False,
            "posts": posts_data,
        }

        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_POSTS_BY_PAGE_AND_TAG)
        self.assertDictEqual(response_json, expected)

    def test_posts_by_page_and_tag_out_of_bound(self):
        tag_name = "tag3"
        invalid_page_nums = (0, 100)
        for page_num in invalid_page_nums:
            response = self.client.get(
                "/resource/posts_by_page_and_tag/{0:s}/{1:d}".format(tag_name, page_num)
            )
            self.assertEqual(response.status_code, RESOURCE_NOT_FOUND_STATUS_CODE)
            self.assertJSONEqual(
                force_str(response.content), RESOURCE_NOT_FOUND_JSON_DATA
            )

    def test_get_post_data_mid(self):
        selected_article_id = 100
        selected_article_index = 99
        article_data = self.article_list[selected_article_index]
        expected = {
            "title": article_data.article.title,
            "created": article_data.article.created.strftime(DATETIME_STR_FORMAT),
            "content": article_data.compiled_data.data,
            "tags": self.sorted_tags_full
            if selected_article_id in self.tag3_article_ids
            else self.sorted_tags_partial,
            "synonym_prev": self.article_list[
                selected_article_index - 1
            ].article.synonym,
            "synonym_next": self.article_list[
                selected_article_index + 1
            ].article.synonym,
        }
        response = self.client.get(
            "/resource/get_post_data/test-article-{0:d}".format(selected_article_id)
        )

        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_GET_POST_DATA)
        self.assertDictEqual(response_json, expected)

    def test_get_post_data_latest(self):
        selected_article_id = self.num_articles
        selected_article_index = self.num_articles - 1
        article_data = self.article_list[selected_article_index]
        expected = {
            "title": article_data.article.title,
            "created": article_data.article.created.strftime(DATETIME_STR_FORMAT),
            "content": article_data.compiled_data.data,
            "tags": self.sorted_tags_full
            if selected_article_id in self.tag3_article_ids
            else self.sorted_tags_partial,
            "synonym_prev": self.article_list[
                selected_article_index - 1
            ].article.synonym,
            "synonym_next": None,
        }
        response = self.client.get(
            "/resource/get_post_data/test-article-{0:d}".format(selected_article_id)
        )

        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_GET_POST_DATA)
        self.assertDictEqual(response_json, expected)

    def test_get_post_data_oldest(self):
        selected_article_id = 1
        selected_article_index = 0
        article_data = self.article_list[selected_article_index]
        expected = {
            "title": article_data.article.title,
            "created": article_data.article.created.strftime(DATETIME_STR_FORMAT),
            "content": article_data.compiled_data.data,
            "tags": self.sorted_tags_full
            if selected_article_id in self.tag3_article_ids
            else self.sorted_tags_partial,
            "synonym_prev": None,
            "synonym_next": self.article_list[
                selected_article_index + 1
            ].article.synonym,
        }
        response = self.client.get(
            "/resource/get_post_data/test-article-{0:d}".format(selected_article_id)
        )

        self.assertEqual(response.status_code, SUCCESS_CODE)
        response_json = response.json()
        validate(response_json, SCHEMA_GET_POST_DATA)
        self.assertDictEqual(response_json, expected)

    def test_get_post_data_not_exist(self):
        response = self.client.get("/resource/get_post_data/non-exist-article")
        self.assertEqual(response.status_code, RESOURCE_NOT_FOUND_STATUS_CODE)
        self.assertJSONEqual(force_str(response.content), RESOURCE_NOT_FOUND_JSON_DATA)

    def test_get_tag_list(self):
        response = self.client.get("/resource/get_tag_list/")
        expected = {
            "data": self.sorted_tags_full,
        }
        self.assertEqual(response.status_code, SUCCESS_CODE)
        validate(response.json(), SCHEMA_GET_TAG_LIST)
        self.assertJSONEqual(force_str(response.content), expected)
