def test_bad_type_content_length(self):
        multipart_parser = MultiPartParser(
            {
                "CONTENT_TYPE": "multipart/form-data; boundary=_foo",
                "CONTENT_LENGTH": "a",
            },
            StringIO("x"),
            [],
            "utf-8",
        )
        self.assertEqual(multipart_parser._content_length, 0)