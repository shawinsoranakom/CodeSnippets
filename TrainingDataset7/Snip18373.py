def test_https_login_url(self):
        quoted_next = quote("http://testserver/login_required/")
        expected = "https:///login/?next=%s" % quoted_next
        self.assertLoginURLEquals(expected)