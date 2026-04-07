def test_upload_name_is_validated(self):
        candidates = [
            "/tmp/",
            "/tmp/..",
            "/tmp/.",
        ]
        if sys.platform == "win32":
            candidates.extend(
                [
                    "c:\\tmp\\",
                    "c:\\tmp\\..",
                    "c:\\tmp\\.",
                ]
            )
        for file_name in candidates:
            with self.subTest(file_name=file_name):
                self.assertRaises(SuspiciousFileOperation, UploadedFile, name=file_name)