from os import listdir, remove
from os.path import join as path_join

from django.test import TestCase
from django.conf import settings

from resource_management.tests.test_utils import use_test_image_dir, TEST_FILE_ROOT_DIR
from resource_management.service.post_update import PostUpdateHandler
from resource_management.models import (
    Article,
    RawArticleData,
    CompiledArticleData,
    ArticleEditHistory,
    Tag,
    ArticleTag,
    Image,
)


class PostUpdateHandlerTestCase(TestCase):
    @use_test_image_dir
    def test_upload_article_create(self):
        synonyms = ("test-article-01", "test-article-02", "test-article-03")
        for synonym in synonyms:
            PostUpdateHandler.upload_article(
                path_join(TEST_FILE_ROOT_DIR, "TestData_01_init.tgz"),
                synonym,
                create_only=True,
            )

        # Three articles with different synonyms
        articles = Article.objects.all()
        self.assertEqual(len(articles), 3)
        article_synonyms = tuple(
            articles.order_by("created").values_list("synonym", flat=True)
        )
        self.assertEqual(article_synonyms, synonyms)

        # Simply count number of raw/compiled doc entries
        raw_data_count = RawArticleData.objects.count()
        self.assertEqual(raw_data_count, 3)
        compiled_data_count = CompiledArticleData.objects.count()
        self.assertEqual(compiled_data_count, 3)

        # Tags
        tags = Tag.objects.all()
        self.assertEqual(len(tags), 3)
        expected_tags = {"tag1", "tag2", "tag3"}
        self.assertEqual(set(tags.values_list("tag_name", flat=True)), expected_tags)
        article_tags_count = ArticleTag.objects.count()
        self.assertEqual(article_tags_count, 9)
        for article in articles:
            owned_tags = {
                a_tag_rel.tag.tag_name for a_tag_rel in article.tags_of_article.all()
            }
            self.assertEqual(owned_tags, expected_tags)

        # Images
        image_count = Image.objects.count()
        self.assertEqual(image_count, 45)  # 3 * 3 * 5 = 45
        expected_resolutions = {
            Image.ImageResolutionType.ORIGINAL,
            Image.ImageResolutionType.LOW,
            Image.ImageResolutionType.MEDIUM,
            Image.ImageResolutionType.LARGE,
            Image.ImageResolutionType.HIGH,
        }
        expected_image_aliases = {"ikea-shark", "red-fox", "drunk-cat"}
        for article in articles:
            for alias in expected_image_aliases:
                image_group = Image.objects.filter(article=article, alias=alias)
                self.assertEqual(image_group.count(), 5)
                self.assertEqual(
                    set(image_group.values_list("resolution", flat=True)),
                    expected_resolutions,
                )

    @use_test_image_dir
    def test_upload_article_update(self):
        synonym = "test-article"
        # Initialize
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_01_init.tgz"),
            synonym,
            create_only=False,
        )
        article = Article.objects.first()
        init_article_timestamp = article.updated
        init_raw_timestamp = RawArticleData.objects.get(article=article).last_update
        init_compile_timestamp = CompiledArticleData.objects.get(
            article=article
        ).last_update

        # Version 2: Title changed
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_02_title.tgz"),
            synonym,
            create_only=False,
        )
        ver2_article = Article.objects.first()
        ver2_article_timestamp = ver2_article.updated
        ver2_raw_data = RawArticleData.objects.get(article=ver2_article)
        ver2_raw_timestamp = ver2_raw_data.last_update
        ver2_compile_timestamp = CompiledArticleData.objects.get(
            article=ver2_article
        ).last_update
        self.assertGreater(ver2_article_timestamp, init_article_timestamp)
        self.assertEqual(ver2_article.title, "Test Article with Title Changed")
        # - No update to XML
        self.assertEqual(init_raw_timestamp, ver2_raw_timestamp)
        self.assertEqual(init_compile_timestamp, ver2_compile_timestamp)
        # - Will leave edit record
        edit_history = ArticleEditHistory.objects.filter(article=ver2_article).order_by(
            "-created"
        )
        self.assertEqual(len(edit_history), 1)
        last_edit = edit_history.first()
        self.assertEqual(last_edit.previous_title, "Test Article")
        self.assertIsNone(last_edit.previous_version)
        self.assertIsNone(last_edit.update_data)
        self.assertIsNone(last_edit.recover_data)

        # Version 3: New tag
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_03_add_tag.tgz"),
            synonym,
            create_only=False,
        )
        ver3_article = Article.objects.first()
        ver3_article_timestamp = ver3_article.updated
        ver3_raw_data = RawArticleData.objects.get(article=ver3_article)
        ver3_raw_timestamp = ver3_raw_data.last_update
        ver3_compile_timestamp = CompiledArticleData.objects.get(
            article=ver3_article
        ).last_update
        self.assertGreater(ver3_article_timestamp, ver2_article_timestamp)
        # - Still no update to XML
        self.assertEqual(init_raw_timestamp, ver3_raw_timestamp)
        self.assertEqual(init_compile_timestamp, ver3_compile_timestamp)
        # - No edit record created
        edit_history = ArticleEditHistory.objects.filter(article=ver3_article).order_by(
            "-created"
        )
        self.assertEqual(len(edit_history), 1)
        # - Check out article-tag relations
        ver3_tag_relations = (
            ArticleTag.objects.filter(article=ver3_article).select_related("tag").all()
        )
        self.assertEqual(len(ver3_tag_relations), 4)
        expected_tags = {"tag1", "tag2", "tag3", "tag4"}
        self.assertSetEqual(
            set(art_tag_rel.tag.tag_name for art_tag_rel in ver3_tag_relations),
            expected_tags,
        )

        # Version 4: Content changed
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_04_content.tgz"),
            synonym,
            create_only=False,
        )
        ver4_article = Article.objects.first()
        ver4_article_timestamp = ver4_article.updated
        ver4_raw_data = RawArticleData.objects.get(article=ver4_article)
        ver4_raw_timestamp = ver4_raw_data.last_update
        ver4_compile_timestamp = CompiledArticleData.objects.get(
            article=ver4_article
        ).last_update
        self.assertGreater(ver4_article_timestamp, ver3_article_timestamp)
        # - XML updated this time
        self.assertGreater(ver4_raw_timestamp, ver3_raw_timestamp)
        self.assertGreater(ver4_compile_timestamp, ver3_compile_timestamp)
        # - Will leave edit record
        edit_history = ArticleEditHistory.objects.filter(article=ver4_article).order_by(
            "-created"
        )
        self.assertEqual(len(edit_history), 2)
        last_edit = edit_history.first()
        self.assertIsNone(last_edit.previous_title)
        self.assertIsNone(last_edit.previous_version)
        self.assertIsNotNone(last_edit.update_data)
        self.assertIsNotNone(last_edit.recover_data)

        # Version 5: Edit on multiple parts
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_05_title_tag_image.tgz"),
            synonym,
            create_only=False,
        )
        ver5_article = Article.objects.first()
        ver5_article_timestamp = ver5_article.updated
        ver5_raw_data = RawArticleData.objects.get(article=ver5_article)
        ver5_raw_timestamp = ver5_raw_data.last_update
        ver5_compile_timestamp = CompiledArticleData.objects.get(
            article=ver5_article
        ).last_update
        self.assertGreater(ver5_article_timestamp, ver4_article_timestamp)
        self.assertEqual(ver5_article.title, "Test Article with Title")
        # - XML updated this time
        self.assertGreater(ver5_raw_timestamp, ver4_raw_timestamp)
        self.assertGreater(ver5_compile_timestamp, ver4_compile_timestamp)
        # - Will leave edit record with file recompiled
        edit_history = ArticleEditHistory.objects.filter(article=ver5_article).order_by(
            "-created"
        )
        self.assertEqual(len(edit_history), 3)
        last_edit = edit_history.first()
        self.assertIsNotNone(last_edit.previous_title)
        self.assertIsNone(last_edit.previous_version)
        self.assertIsNotNone(last_edit.update_data)
        self.assertIsNotNone(last_edit.recover_data)
        # - Check out tag / article-tag relations
        self.assertEqual(Tag.objects.count(), 5)
        ver5_tag_relations = (
            ArticleTag.objects.filter(article=ver5_article).select_related("tag").all()
        )
        self.assertEqual(len(ver5_tag_relations), 3)
        expected_tags = {"tag1", "tag2", "tag5"}
        self.assertSetEqual(
            set(art_tag_rel.tag.tag_name for art_tag_rel in ver5_tag_relations),
            expected_tags,
        )
        # - Simply check out number of image entries
        self.assertEqual(Image.objects.filter(article=ver5_article).count(), 10)
        self.assertEqual(Image.all_objects.filter(article=ver5_article).count(), 15)

        # Version 6: Add/update images
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_06_image.tgz"),
            synonym,
            create_only=False,
        )
        ver6_article = Article.objects.first()
        ver6_article_timestamp = ver6_article.updated
        ver6_raw_data = RawArticleData.objects.get(article=ver6_article)
        ver6_raw_timestamp = ver6_raw_data.last_update
        ver6_compile_timestamp = CompiledArticleData.objects.get(
            article=ver6_article
        ).last_update
        self.assertGreater(ver6_article_timestamp, ver5_article_timestamp)
        # - XML updated (both raw Markdown and images are changed)
        self.assertGreater(ver6_raw_timestamp, ver5_raw_timestamp)
        self.assertGreater(ver6_compile_timestamp, ver5_compile_timestamp)
        # - Will leave edit record with file recompiled
        edit_history = ArticleEditHistory.objects.filter(article=ver6_article).order_by(
            "-created"
        )
        self.assertEqual(len(edit_history), 4)
        last_edit = edit_history.first()
        self.assertIsNone(last_edit.previous_title)
        self.assertIsNone(last_edit.previous_version)
        self.assertIsNotNone(last_edit.update_data)
        self.assertIsNotNone(last_edit.recover_data)
        # - Simply check out number of image entries
        available_images = Image.objects.filter(article=ver6_article)
        expected_aliases = {"drunk-cat", "rabbit-carrot", "red-fox"}
        self.assertSetEqual(
            set(image.alias for image in available_images), expected_aliases
        )
        removed_images = Image.deleted_objects.filter(article=ver6_article)
        aliases_with_delete_history = {"drunk-cat", "ikea-shark"}
        self.assertSetEqual(
            set(image.alias for image in removed_images), aliases_with_delete_history
        )
        # Available entries = 3 * 5; Removed entries = 2 * 5
        self.assertEqual(Image.objects.filter(article=ver6_article).count(), 15)
        self.assertEqual(Image.deleted_objects.filter(article=ver6_article).count(), 10)

    @use_test_image_dir
    def test_upload_article_no_update(self):
        synonym = "test-article"
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_01_init.tgz"),
            synonym,
            create_only=False,
        )
        article = Article.objects.first()
        article_timestamp = article.updated
        raw_data = RawArticleData.objects.get(article=article)
        raw_timestamp = raw_data.last_update
        compile_timestamp = CompiledArticleData.objects.get(article=article).last_update

        # Run again
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_01_init.tgz"),
            synonym,
            create_only=False,
        )
        article_new = Article.objects.first()
        article_new_timestamp = article_new.updated
        raw_data_new = RawArticleData.objects.get(article=article_new)
        raw_new_timestamp = raw_data_new.last_update
        compile_new_timestamp = CompiledArticleData.objects.get(
            article=article_new
        ).last_update

        self.assertEqual(article_timestamp, article_new_timestamp)
        self.assertEqual(raw_timestamp, raw_new_timestamp)
        self.assertEqual(compile_timestamp, compile_new_timestamp)
        # - Will leave edit record with file recompiled
        edit_history = ArticleEditHistory.objects.filter(article=article_new).order_by(
            "-created"
        )
        self.assertFalse(edit_history)

    @use_test_image_dir
    def test_upload_article_duplicated_synonym(self):
        synonym = "test-article"
        PostUpdateHandler.upload_article(
            path_join(TEST_FILE_ROOT_DIR, "TestData_01_init.tgz"),
            synonym,
            create_only=True,
        )
        self.assertRaises(
            ValueError,
            PostUpdateHandler.upload_article,
            path_join(TEST_FILE_ROOT_DIR, "TestData_01_init.tgz"),
            synonym,
            create_only=True,
        )

    def tearDown(self):
        # Simply remove all the files in this directory
        for dir_path in (
            settings.OPENED_IMAGE_DIR_TEST,
            settings.PROTECTED_IMAGE_DIR_TEST,
        ):
            for filename in listdir(dir_path):
                remove(path_join(dir_path, filename))
