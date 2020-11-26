from functools import cached_property
from typing import NamedTuple, final

from diff_match_patch import diff_match_patch

__all__ = ["PatchResult", "DocumentPatchCreator"]


@final
class PatchResult(NamedTuple):
    update_patch: str
    recover_patch: str


@final
class DocumentPatchCreator(object):
    @cached_property
    def dmp(self) -> diff_match_patch:
        return diff_match_patch()

    def _create_patch_file(self, text_1: str, text_2: str) -> str:
        """Return unidiff patch that converts text_1 to text_2."""
        return self.dmp.patch_toText(
            self.dmp.patch_make(self.dmp.diff_lineMode(text_1, text_2, None))
        )

    def create_patch_files(self, original_file: str, updated_file: str) -> PatchResult:
        return PatchResult(
            update_patch=self._create_patch_file(original_file, updated_file),
            recover_patch=self._create_patch_file(updated_file, original_file),
        )
