def test_get_max_fields_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_NUMBER_FIELDS=1):
            with self.assertRaisesMessage(TooManyFieldsSent, TOO_MANY_FIELDS_MSG):
                request = WSGIRequest(
                    {
                        "REQUEST_METHOD": "GET",
                        "wsgi.input": BytesIO(b""),
                        "QUERY_STRING": "a=1&a=2&a=3",
                    }
                )
                request.GET["a"]