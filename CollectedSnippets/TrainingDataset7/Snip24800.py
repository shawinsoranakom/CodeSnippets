def test_newlines_in_headers(self):
        # Bug #10188: Do not allow newlines in headers (CR or LF)
        r = HttpResponse()
        with self.assertRaises(BadHeaderError):
            r.headers.__setitem__("test\rstr", "test")
        with self.assertRaises(BadHeaderError):
            r.headers.__setitem__("test\nstr", "test")