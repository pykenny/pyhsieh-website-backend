from django.http import JsonResponse
from django.views.decorators.http import require_GET

import resource_management.service.image as image_service
from .utils import json_404_on_error


@require_GET
@json_404_on_error
def get_full_file_path(_, filename):
    return JsonResponse(image_service.get_full_file_path(filename))
