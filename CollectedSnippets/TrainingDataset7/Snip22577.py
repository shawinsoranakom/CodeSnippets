def test_recursive_folders_without_files(self):
        f = FilePathField(
            path=self.path, recursive=True, allow_folders=True, allow_files=False
        )
        self.assertChoices(
            f,
            [
                ("/filepathfield_test_dir/c", "c"),
                ("/filepathfield_test_dir/h", "h"),
                ("/filepathfield_test_dir/j", "j"),
                ("/filepathfield_test_dir/c/f", "c/f"),
            ],
        )