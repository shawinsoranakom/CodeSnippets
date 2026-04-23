def test_POST_form_data_json(self):
        payload = FakePayload(
            "\r\n".join([f"--{BOUNDARY}", *self._json_payload, f"--{BOUNDARY}--"])
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
                "JSON": [
                    '{"pk": 1, "model": "store.book", "fields": {"name": "Mostly '
                    'Harmless", "author": ["Douglas", Adams"]}}'
                ],
            },
        )