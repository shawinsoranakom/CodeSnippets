def test_storage_dangerous_paths(self):
        candidates = [
            ("/tmp/..", ".."),
            ("\\tmp\\..", ".."),
            ("/tmp/.", "."),
            ("\\tmp\\.", "."),
            ("..", ".."),
            (".", "."),
            ("", ""),
        ]
        s = FileSystemStorage()
        s_overwrite = FileSystemStorage(allow_overwrite=True)
        msg = "Could not derive file name from '%s'"
        for file_name, base_name in candidates:
            with self.subTest(file_name=file_name):
                with self.assertRaisesMessage(SuspiciousFileOperation, msg % base_name):
                    s.get_available_name(file_name)
                with self.assertRaisesMessage(SuspiciousFileOperation, msg % base_name):
                    s_overwrite.get_available_name(file_name)
                with self.assertRaisesMessage(SuspiciousFileOperation, msg % base_name):
                    s.generate_filename(file_name)