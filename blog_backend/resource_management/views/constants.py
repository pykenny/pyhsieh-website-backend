from http import HTTPStatus

SUCCESS_CODE = HTTPStatus.OK
RESOURCE_NOT_FOUND_STATUS_CODE = HTTPStatus.NOT_FOUND

RESOURCE_NOT_FOUND_JSON_DATA = {
    "message": "Can not find the requested data",
}

PAGE_SIZE = 10
