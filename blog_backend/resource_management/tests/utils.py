from os.path import dirname, join as path_join

from django.conf import settings
from django.test import override_settings

TEST_FILE_ROOT_DIR = path_join(dirname(__file__), "files")


def use_test_image_dir(f):
    return override_settings(
        OPENED_IMAGE_GROUP=settings.OPENED_IMAGE_GROUP_TEST,
        PROTECTED_IMAGE_GROUP=settings.PROTECTED_IMAGE_GROUP_TEST,
        OPENED_IMAGE_DIR=settings.OPENED_IMAGE_DIR_TEST,
        PROTECTED_IMAGE_DIR=settings.PROTECTED_IMAGE_DIR_TEST,
    )(f)
