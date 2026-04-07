def test_filefield_generate_filename_upload_to_absolute_path(self):
        def upload_to(instance, filename):
            return "/tmp/" + filename

        f = FileField(upload_to=upload_to)
        candidates = [
            "path",
            "../path",
            "???",
            "$.$.$",
        ]
        for file_name in candidates:
            msg = f"Detected path traversal attempt in '/tmp/{file_name}'"
            with self.subTest(file_name=file_name):
                with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                    f.generate_filename(None, file_name)