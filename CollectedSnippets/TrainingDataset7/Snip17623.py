def test_get_user_anonymous(self):
        request = HttpRequest()
        request.session = self.client.session
        user = get_user(request)
        self.assertIsInstance(user, AnonymousUser)