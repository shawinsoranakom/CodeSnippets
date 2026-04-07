def test_file_upload_temp_dir_pathlib(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with override_settings(FILE_UPLOAD_TEMP_DIR=Path(tmp_dir)):
                with TemporaryUploadedFile(
                    "test.txt", "text/plain", 1, "utf-8"
                ) as temp_file:
                    self.assertTrue(os.path.exists(temp_file.file.name))