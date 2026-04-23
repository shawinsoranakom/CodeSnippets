def test_set_with_xheader_wrong(self):
        req = HttpRequest()
        req.META["HTTP_X_FORWARDED_PROTO"] = "wrongvalue"
        self.assertIs(req.is_secure(), False)