def test_view_with_bad_login(self):
        "Request a page that is protected with @login, but use bad credentials"

        login = self.client.login(username="otheruser", password="nopassword")
        self.assertFalse(login)