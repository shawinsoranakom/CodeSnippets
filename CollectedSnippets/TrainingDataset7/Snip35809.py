def test_redirect_to_url(self):
        res = redirect("/foo/")
        self.assertEqual(res.url, "/foo/")
        res = redirect("http://example.com/")
        self.assertEqual(res.url, "http://example.com/")
        # Assert that we can redirect using UTF-8 strings
        res = redirect("/æøå/abc/")
        self.assertEqual(res.url, "/%C3%A6%C3%B8%C3%A5/abc/")
        # Assert that no imports are attempted when dealing with a relative
        # path (previously, the below would resolve in a UnicodeEncodeError
        # from __import__ )
        res = redirect("/æøå.abc/")
        self.assertEqual(res.url, "/%C3%A6%C3%B8%C3%A5.abc/")
        res = redirect("os.path")
        self.assertEqual(res.url, "os.path")