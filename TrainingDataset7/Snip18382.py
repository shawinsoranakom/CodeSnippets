def test_redirect_to_login_with_lazy(self):
        login_redirect_response = redirect_to_login(next="/else/where/")
        expected = "/login/?next=/else/where/"
        self.assertEqual(expected, login_redirect_response.url)