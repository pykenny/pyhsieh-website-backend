##########################
#  JSON Response Schema  #
##########################
SCHEMA_POSTS_BY_PAGE = {
    "type": "object",
    "properties": {
        "page_num": {"type": "integer", "minimum": 1},
        "tag": {"type": ["string", "null"]},
        "has_next_page": {"type": "boolean"},
        "has_prev_page": {"type": "boolean"},
        "posts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "synonym": {"type": "string"},
                    "created": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string", "uniqueItems": True},
                    },
                },
                "required": ["title", "synonym", "created", "tags"],
            },
        },
    },
    "required": ["page_num", "has_next_page", "has_prev_page", "posts"],
}

SCHEMA_POSTS_BY_PAGE_AND_TAG = SCHEMA_POSTS_BY_PAGE

SCHEMA_GET_POST_DATA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "created": {"type": "string"},
        "content": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
        "synonym_prev": {"type": ["string", "null"]},
        "synonym_next": {"type": ["string", "null"]},
    },
    "required": ["title", "created", "content", "tags", "synonym_prev", "synonym_next"],
}

SCHEMA_GET_TAG_LIST = {
    "type": "object",
    "properties": {
        "data": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        }
    },
    "required": ["data"],
}

DATETIME_STR_FORMAT = "%Y%m%d-%H%m%S"
