def test_set_with_xheader_leftmost_not_secure(self):
        req = HttpRequest()
        req.META["HTTP_X_FORWARDED_PROTO"] = "http, https"
        self.assertIs(req.is_secure(), False)