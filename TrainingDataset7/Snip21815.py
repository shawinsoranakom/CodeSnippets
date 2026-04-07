def test_filefield_generate_filename_absolute_path(self):
        f = FileField(upload_to="some/folder/")
        candidates = [
            "/tmp/path",
            "/tmp/../path",
        ]
        for file_name in candidates:
            msg = f"Detected path traversal attempt in '{file_name}'"
            with self.subTest(file_name=file_name):
                with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                    f.generate_filename(None, file_name)