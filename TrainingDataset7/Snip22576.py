def test_recursive_no_folders_or_files(self):
        f = FilePathField(
            path=self.path, recursive=True, allow_folders=False, allow_files=False
        )
        self.assertChoices(f, [])