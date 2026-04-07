def test_data_upload_max_number_files_exceeded(self):
        payload = FakePayload(
            encode_multipart(
                BOUNDARY,
                {
                    "a.txt": "Hello World!",
                    "b.txt": "Hello Django!",
                    "c.txt": "Hello Python!",
                },
            )
        )
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": MULTIPART_CONTENT,
            "CONTENT_LENGTH": len(payload),
            "wsgi.input": payload,
            "SERVER_NAME": "test",
            "SERVER_PORT": "8000",
        }

        response = WSGIHandler()(environ, lambda *a, **k: None)
        self.assertEqual(response.status_code, 400)