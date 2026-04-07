def test_storage_dangerous_paths_dir_name(self):
        candidates = [
            ("../path", ".."),
            ("..\\path", ".."),
            ("tmp/../path", "tmp/.."),
            ("tmp\\..\\path", "tmp/.."),
            ("/tmp/../path", "/tmp/.."),
            ("\\tmp\\..\\path", "/tmp/.."),
        ]
        s = FileSystemStorage()
        s_overwrite = FileSystemStorage(allow_overwrite=True)
        for file_name, path in candidates:
            msg = "Detected path traversal attempt in '%s'" % path
            with self.subTest(file_name=file_name):
                with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                    s.get_available_name(file_name)
                with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                    s_overwrite.get_available_name(file_name)
                with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                    s.generate_filename(file_name)