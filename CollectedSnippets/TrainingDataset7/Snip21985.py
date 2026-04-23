def test_negative_content_length(self):
        with self.assertRaisesMessage(
            MultiPartParserError, "Invalid content length: -1"
        ):
            MultiPartParser(
                {
                    "CONTENT_TYPE": "multipart/form-data; boundary=_foo",
                    "CONTENT_LENGTH": -1,
                },
                StringIO("x"),
                [],
                "utf-8",
            )