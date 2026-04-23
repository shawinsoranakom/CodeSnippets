def test_redirect_to_login_with_lazy_and_unicode(self):
        login_redirect_response = redirect_to_login(next="/else/where/झ/")
        expected = "/login/?next=/else/where/%E0%A4%9D/"
        self.assertEqual(expected, login_redirect_response.url)