def test_set_with_xheader_leftmost_right(self):
        req = HttpRequest()
        req.META["HTTP_X_FORWARDED_PROTO"] = "https, http"
        self.assertIs(req.is_secure(), True)
        req.META["HTTP_X_FORWARDED_PROTO"] = "https  , http"
        self.assertIs(req.is_secure(), True)