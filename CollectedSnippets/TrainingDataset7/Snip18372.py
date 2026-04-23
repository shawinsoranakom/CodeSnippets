def test_remote_login_url(self):
        quoted_next = quote("http://testserver/login_required/")
        expected = "http://remote.example.com/login?next=%s" % quoted_next
        self.assertLoginURLEquals(expected)