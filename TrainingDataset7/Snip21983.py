def test_empty_upload_handlers(self):
        # We're not actually parsing here; just checking if the parser properly
        # instantiates with empty upload handlers.
        MultiPartParser(
            {
                "CONTENT_TYPE": "multipart/form-data; boundary=_foo",
                "CONTENT_LENGTH": "1",
            },
            StringIO("x"),
            [],
            "utf-8",
        )