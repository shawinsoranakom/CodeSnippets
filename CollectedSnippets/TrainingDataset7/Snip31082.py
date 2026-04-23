def test_non_utf8_charset_POST_bad_request(self):
        payload = FakePayload(urlencode({"key": "España".encode("latin-1")}))
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_LENGTH": len(payload),
                "CONTENT_TYPE": "application/x-www-form-urlencoded; charset=iso-8859-1",
                "wsgi.input": payload,
            }
        )
        msg = (
            "HTTP requests with the 'application/x-www-form-urlencoded' content type "
            "must be UTF-8 encoded."
        )
        with self.assertRaisesMessage(BadRequest, msg):
            request.POST
        with self.assertRaisesMessage(BadRequest, msg):
            request.FILES