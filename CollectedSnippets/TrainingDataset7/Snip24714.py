def test_bad_path_info(self):
        """
        A non-UTF-8 path populates PATH_INFO with an URL-encoded path and
        produces a 404.
        """
        environ = self.request_factory.get("/").environ
        environ["PATH_INFO"] = "\xed"
        handler = WSGIHandler()
        response = handler(environ, lambda *a, **k: None)
        # The path of the request will be encoded to '/%ED'.
        self.assertEqual(response.status_code, 404)