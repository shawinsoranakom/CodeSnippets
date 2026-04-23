def test_user_login(self):
        auth.login(self.request, self.user)
        self.assertEqual(self.request.session[auth.SESSION_KEY], str(self.user.pk))