def test_multipart_parser_class_immutable_after_parse(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    "--boundary",
                    'Content-Disposition: form-data; name="name"',
                    "",
                    "value",
                    "--boundary--",
                ]
            )
        )
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data; boundary=boundary",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )

        # Access POST to trigger parsing.
        request.POST

        msg = (
            "You cannot set the multipart parser class after the upload has been "
            "processed."
        )
        with self.assertRaisesMessage(RuntimeError, msg):
            request.multipart_parser_class = MultiPartParser