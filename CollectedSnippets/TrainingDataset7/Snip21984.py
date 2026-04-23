def test_invalid_content_type(self):
        with self.assertRaisesMessage(
            MultiPartParserError, "Invalid Content-Type: text/plain"
        ):
            MultiPartParser(
                {
                    "CONTENT_TYPE": "text/plain",
                    "CONTENT_LENGTH": "1",
                },
                StringIO("x"),
                [],
                "utf-8",
            )