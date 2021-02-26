from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from resource_management.views.utils import json_404_on_error
from resource_management.views.constants import (
    RESOURCE_NOT_FOUND_STATUS_CODE,
    RESOURCE_NOT_FOUND_JSON_DATA,
)


class ViewUtilsTestCase(TestCase):
    @staticmethod
    def not_found_operation():
        raise ObjectDoesNotExist()

    def test_json_404_on_error(self):
        wrapped_function = json_404_on_error(self.not_found_operation)
        response = wrapped_function()
        self.assertEqual(response.status_code, RESOURCE_NOT_FOUND_STATUS_CODE)
        self.assertJSONEqual(
            response.content.decode("utf-8"), RESOURCE_NOT_FOUND_JSON_DATA
        )
