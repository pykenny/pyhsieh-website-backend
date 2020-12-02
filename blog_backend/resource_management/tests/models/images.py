from django.test import TestCase

from resource_management.models import Article, Image


class ImageModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.article = Article.objects.create(
            synonym="test-article",
            title="Test Article",
        )
        cls.image_data = Image.objects.create(
            article=cls.article,
            alias="example-image",
            extension="jpg",
            resolution=Image.ImageResolutionType.ORIGINAL,
            height=400,
            width=400,
        )

    def test_file_name(self):
        image_uuid_str = str(self.image_data.uuid)
        self.assertEqual(self.image_data.file_name, image_uuid_str + ".jpg")
