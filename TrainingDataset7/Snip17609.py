def test_get_user(self):
        self.client.force_login(self.user)
        request = HttpRequest()
        request.session = self.client.session
        user = get_user(request)
        self.assertEqual(user, self.user)