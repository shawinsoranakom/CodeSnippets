def test_set_without_xheader(self):
        req = HttpRequest()
        self.assertIs(req.is_secure(), False)