def test_allow_folders(self):
        f = FilePathField(path=self.path, allow_folders=True, allow_files=False)
        self.assertChoices(
            f,
            [
                ("/filepathfield_test_dir/c", "c"),
                ("/filepathfield_test_dir/h", "h"),
                ("/filepathfield_test_dir/j", "j"),
            ],
        )