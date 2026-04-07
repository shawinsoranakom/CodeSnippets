def test_filefield_dangerous_filename(self):
        candidates = [
            ("..", "some/folder/.."),
            (".", "some/folder/."),
            ("", "some/folder/"),
            ("???", "???"),
            ("$.$.$", "$.$.$"),
        ]
        f = FileField(upload_to="some/folder/")
        for file_name, msg_file_name in candidates:
            msg = f"Could not derive file name from '{msg_file_name}'"
            with self.subTest(file_name=file_name):
                with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                    f.generate_filename(None, file_name)