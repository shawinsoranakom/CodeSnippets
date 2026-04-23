def test_filefield_generate_filename_upload_to_dangerous_filename(self):
        def upload_to(instance, filename):
            return "/tmp/" + filename

        f = FileField(upload_to=upload_to)
        candidates = ["..", ".", ""]
        for file_name in candidates:
            msg = f"Could not derive file name from '/tmp/{file_name}'"
            with self.subTest(file_name=file_name):
                with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                    f.generate_filename(None, file_name)