from os.path import expanduser
from re import match
from django.core.management.base import BaseCommand, CommandError
from resource_management.service.post_update import PostUpdateHandler


class Command(BaseCommand):
    _SYNONYM_REGEX = r"^[a-z0-9][a-z0-9\\-]+[a-z0-9]$"

    help = (
        "Upload post from bundled post data to create new post, "
        "or update existing post."
    )

    def add_arguments(self, parser):
        parser.add_argument("archive-path", type=str, help="Path to tar bundle file.")
        parser.add_argument(
            "--synonym",
            dest="synonym",
            type=str,
            required=True,
            help="Article's synonym and will be used in article's URL. "
            "Only lower-case alphabets, digits, and hyphen ('-') can be used in synonym, "
            "plus it can't start or end with a hyphen.",
        )
        parser.add_argument(
            "--new",
            dest="new_article",
            action="store_true",
            help="Only create new article and stop when the synonym is already "
            "used by existing article.",
        )

    def handle(self, *args, **options):
        if not self._is_valid_synonym(options["synonym"]):
            raise CommandError(
                "'{:s}' is not a valid article synonym.".format(options["synonym"])
            )
        PostUpdateHandler.upload_article(
            expanduser(options["archive-path"]),
            options["synonym"],
            create_only=options["new_article"],
        )

    @classmethod
    def _is_valid_synonym(cls, s: str) -> bool:
        return match(cls._SYNONYM_REGEX, s) is not None
