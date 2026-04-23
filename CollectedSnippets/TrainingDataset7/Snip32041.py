def test_none(self):
        req = HttpRequest()
        self.assertIs(req.is_secure(), False)