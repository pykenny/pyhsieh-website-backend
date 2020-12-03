from functools import wraps

from django.http import JsonResponse

from .constants import RESOURCE_NOT_FOUND_STATUS_CODE, RESOURCE_NOT_FOUND_JSON_DATA


def json_404_on_error(view_fn):
    """ Wrapper function to return JSON 404 template response """

    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        try:
            return view_fn(*args, **kwargs)
        except Exception:
            return JsonResponse(
                RESOURCE_NOT_FOUND_JSON_DATA, status=RESOURCE_NOT_FOUND_STATUS_CODE
            )

    return wrapper
