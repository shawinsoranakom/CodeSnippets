def test_backend_path(self):
        username = "username"
        password = "password"
        User.objects.create_user(username, "email", password)
        self.assertTrue(self.client.login(username=username, password=password))
        request = HttpRequest()
        request.session = self.client.session
        self.assertEqual(request.session[BACKEND_SESSION_KEY], self.backend)