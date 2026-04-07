def test_get_max_fields_not_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_NUMBER_FIELDS=3):
            request = WSGIRequest(
                {
                    "REQUEST_METHOD": "GET",
                    "wsgi.input": BytesIO(b""),
                    "QUERY_STRING": "a=1&a=2&a=3",
                }
            )
            request.GET["a"]