def test_malformed_multipart_header(self):
        tests = [
            ('Content-Disposition : form-data; name="name"', {"name": ["value"]}),
            ('Content-Disposition:form-data; name="name"', {"name": ["value"]}),
            ('Content-Disposition :form-data; name="name"', {"name": ["value"]}),
            # The invalid encoding causes the entire part to be skipped.
            (
                'Content-Disposition: form-data; name="name"; '
                "filename*=BOGUS''test%20file.txt",
                {},
            ),
        ]
        for header, expected_post in tests:
            with self.subTest(header):
                payload = FakePayload(
                    "\r\n".join(
                        [
                            "--boundary",
                            header,
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
                self.assertEqual(request.POST, expected_post)