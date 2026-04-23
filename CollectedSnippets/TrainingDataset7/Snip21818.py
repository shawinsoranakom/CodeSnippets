def test_filefield_generate_filename_upload_to_overrides_dangerous_filename(self):
        def upload_to(instance, filename):
            return "test.txt"

        f = FileField(upload_to=upload_to)
        candidates = [
            "/tmp/.",
            "/tmp/..",
            "/tmp/../path",
            "/tmp/path",
            "some/folder/",
            "some/folder/.",
            "some/folder/..",
            "some/folder/???",
            "some/folder/$.$.$",
            "some/../test.txt",
            "",
        ]
        for file_name in candidates:
            with self.subTest(file_name=file_name):
                self.assertEqual(f.generate_filename(None, file_name), "test.txt")