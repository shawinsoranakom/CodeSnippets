def test_body_after_POST_multipart_related(self):
        """
        Reading body after parsing multipart that isn't form-data is allowed
        """
        # Ticket #9054
        # There are cases in which the multipart data is related instead of
        # being a binary upload, in which case it should still be accessible
        # via body.
        payload_data = b"\r\n".join(
            [
                b"--boundary",
                b'Content-ID: id; name="name"',
                b"",
                b"value",
                b"--boundary--",
            ]
        )
        payload = FakePayload(payload_data)
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/related; boundary=boundary",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        self.assertEqual(request.POST, {})
        self.assertEqual(request.body, payload_data)