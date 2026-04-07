def test_POST_content_type_json(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    '{"pk": 1, "model": "store.book", "fields": {"name": "Mostly Ha',
                    'rmless", "author": ["Douglas", Adams"]}}',
                ]
            )
        )
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "application/json",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        self.assertEqual(request.POST, {})
        self.assertEqual(request.FILES, {})