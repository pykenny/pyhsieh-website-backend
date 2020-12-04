from os.path import join as path_join

from django.test import TestCase
from django.conf import settings

from jsonschema import validate

from resource_management.models import (
    Article,
    Image,
)
from resource_management.views.constants import (
    RESOURCE_NOT_FOUND_STATUS_CODE,
    RESOURCE_NOT_FOUND_JSON_DATA,
    SUCCESS_CODE,
)
from .constants import (
    SCHEMA_IMAGES_GET_FULL_FILE_PATH,
)
from ..test_utils import use_test_image_dir


class ViewImagesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.article = Article.objects.create(
            synonym="test-article",
            title="Test Article",
        )
        image_alias = "test-image"
        image_ext = "jpg"
        cls.opened_image = Image.objects.create(
            article=cls.article,
            alias=image_alias,
            extension=image_ext,
            resolution=Image.ImageResolutionType.MEDIUM,
            height=100,
            width=100,
        )
        cls.protected_image = Image.objects.create(
            article=cls.article,
            alias=image_alias,
            extension=image_ext,
            resolution=Image.ImageResolutionType.ORIGINAL,
            height=100,
            width=100,
        )
        cls.opened_image_file_name = "{name:s}.{ext:s}".format(
            name=str(cls.opened_image.uuid),
            ext=cls.opened_image.extension,
        )
        cls.protected_image_file_name = "{name:s}.{ext:s}".format(
            name=str(cls.protected_image.uuid),
            ext=cls.protected_image.extension,
        )

    @use_test_image_dir
    def test_get_full_file_path_opened(self):
        response = self.client.get(
            "/resource/get_full_file_path/{0:s}".format(
                self.opened_image_file_name,
            )
        )
        response_json = response.json()
        expected = {
            "data": path_join(settings.OPENED_IMAGE_DIR, self.opened_image_file_name)
        }
        self.assertEqual(response.status_code, SUCCESS_CODE)
        validate(response_json, SCHEMA_IMAGES_GET_FULL_FILE_PATH)
        self.assertDictEqual(response_json, expected)

    def test_get_full_file_path_protected(self):
        response = self.client.get(
            "/resource/get_full_file_path/{0:s}".format(
                self.protected_image_file_name,
            )
        )
        response_json = response.json()
        self.assertEqual(response.status_code, RESOURCE_NOT_FOUND_STATUS_CODE)
        self.assertDictEqual(
            response_json,
            RESOURCE_NOT_FOUND_JSON_DATA,
        )

    def test_get_full_file_path_non_exist(self):
        response = self.client.get("/resource/get_full_file_path/some-other-file.jpg")
        response_json = response.json()
        self.assertEqual(response.status_code, RESOURCE_NOT_FOUND_STATUS_CODE)
        self.assertDictEqual(
            response_json,
            RESOURCE_NOT_FOUND_JSON_DATA,
        )
