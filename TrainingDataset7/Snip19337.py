def test_file_upload_temp_dir_nonexistent(self):
        for setting in ["nonexistent", Path("nonexistent")]:
            with self.subTest(setting), self.settings(FILE_UPLOAD_TEMP_DIR=setting):
                self.assertEqual(
                    check_setting_file_upload_temp_dir(None),
                    [
                        Error(
                            "The FILE_UPLOAD_TEMP_DIR setting refers to the "
                            "nonexistent directory 'nonexistent'.",
                            id="files.E001",
                        ),
                    ],
                )