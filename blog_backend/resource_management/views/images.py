from django.http import JsonResponse
from django.views.decorators.http import require_GET

from resource_management.service.image import (
    get_full_file_path as get_full_file_path_service,
)


@require_GET
def get_full_file_path(_, filename):
    return JsonResponse(get_full_file_path_service(filename))
