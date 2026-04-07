def get_suspicious_environ(self):
        payload = FakePayload("a=1&a=2&a=3\r\n")
        return {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "CONTENT_LENGTH": len(payload),
            "wsgi.input": payload,
            "SERVER_NAME": "test",
            "SERVER_PORT": "8000",
        }