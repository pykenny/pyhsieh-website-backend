from django.test import TestCase

from resource_management.utils.articles import DocumentPatchCreator, PatchResult

from diff_match_patch import diff_match_patch


class DocumentPatchCreatorTestCase(TestCase):
    def setUp(self):
        self.file_1 = "# Article\nHere's some test text."
        self.file_2 = "# Article\nHere's some test text for file 2.\nSome more content."
        self.patch_creator = DocumentPatchCreator()
        self.dmp = diff_match_patch()
        self.forward_line_level_diff = self.dmp.diff_lineMode(
            self.file_1, self.file_2, None
        )
        self.forward_line_level_patch = self.dmp.patch_make(
            self.forward_line_level_diff
        )
        self.forward_text_patch = self.dmp.patch_toText(self.forward_line_level_patch)
        self.backward_line_level_diff = self.dmp.diff_lineMode(
            self.file_2, self.file_1, None
        )
        self.backward_line_level_patch = self.dmp.patch_make(
            self.backward_line_level_diff
        )
        self.backward_text_patch = self.dmp.patch_toText(self.backward_line_level_patch)

    def test__create_patch_file(self):
        output = self.patch_creator._create_patch_file(self.file_1, self.file_2)
        self.assertEqual(output, self.forward_text_patch)
        output = self.patch_creator._create_patch_file(self.file_2, self.file_1)
        self.assertEqual(output, self.backward_text_patch)

    def test_create_patch_files(self):
        expected = PatchResult(
            update_patch=self.forward_text_patch,
            recover_patch=self.backward_text_patch,
        )
        output = self.patch_creator.create_patch_files(self.file_1, self.file_2)
        self.assertEqual(output, expected)
