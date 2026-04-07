def setUp(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    "--boundary",
                    'Content-Disposition: form-data; name="name1"',
                    "",
                    "value1",
                    "--boundary",
                    'Content-Disposition: form-data; name="name2"',
                    "",
                    "value2",
                    "--boundary--",
                ]
            )
        )
        self.request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data; boundary=boundary",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )