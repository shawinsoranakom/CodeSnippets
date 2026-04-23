def test_set_with_xheader_right(self):
        req = HttpRequest()
        req.META["HTTP_X_FORWARDED_PROTO"] = "https"
        self.assertIs(req.is_secure(), True)