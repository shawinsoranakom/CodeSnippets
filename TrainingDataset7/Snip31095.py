def test_POST_multipart_with_file(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    f"--{BOUNDARY}",
                    'Content-Disposition: form-data; name="name"',
                    "",
                    "value",
                    f"--{BOUNDARY}",
                    *self._json_payload,
                    f"--{BOUNDARY}",
                    'Content-Disposition: form-data; name="File"; filename="test.csv"',
                    "Content-Type: application/octet-stream",
                    "",
                    "Framework,ID",
                    "Django,1",
                    "Flask,2",
                    f"--{BOUNDARY}--",
                ]
            )
        )
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": MULTIPART_CONTENT,
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        self.assertEqual(
            request.POST,
            {
                "name": ["value"],
                "JSON": [
                    '{"pk": 1, "model": "store.book", "fields": {"name": "Mostly '
                    'Harmless", "author": ["Douglas", Adams"]}}'
                ],
            },
        )
        self.assertEqual(len(request.FILES), 1)
        self.assertIsInstance((request.FILES["File"]), InMemoryUploadedFile)