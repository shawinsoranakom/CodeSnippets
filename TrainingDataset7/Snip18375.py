def test_remote_login_url_with_next_querystring(self):
        quoted_next = quote("http://testserver/login_required/")
        expected = "http://remote.example.com/login/?next=%s" % quoted_next
        self.assertLoginURLEquals(expected)