def test_sanitize_file_name(self):
        parser = MultiPartParser(
            {
                "CONTENT_TYPE": "multipart/form-data; boundary=_foo",
                "CONTENT_LENGTH": "1",
            },
            StringIO("x"),
            [],
            "utf-8",
        )
        for file_name in CANDIDATE_TRAVERSAL_FILE_NAMES:
            with self.subTest(file_name=file_name):
                self.assertEqual(parser.sanitize_file_name(file_name), "hax0rd.txt")