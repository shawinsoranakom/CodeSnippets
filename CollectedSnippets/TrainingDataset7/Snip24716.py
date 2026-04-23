def test_non_ascii_cookie(self):
        """
        Non-ASCII cookies set in JavaScript are properly decoded (#20557).
        """
        environ = self.request_factory.get("/").environ
        raw_cookie = 'want="café"'.encode("utf-8").decode("iso-8859-1")
        environ["HTTP_COOKIE"] = raw_cookie
        request = WSGIRequest(environ)
        self.assertEqual(request.COOKIES["want"], "café")