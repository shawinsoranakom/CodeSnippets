def test_invalid_unicode_cookie(self):
        """
        Invalid cookie content should result in an absent cookie, but not in a
        crash while trying to decode it (#23638).
        """
        environ = self.request_factory.get("/").environ
        environ["HTTP_COOKIE"] = "x=W\x03c(h]\x8e"
        request = WSGIRequest(environ)
        # We don't test COOKIES content, as the result might differ between
        # Python version because parsing invalid content became stricter in
        # latest versions.
        self.assertIsInstance(request.COOKIES, dict)