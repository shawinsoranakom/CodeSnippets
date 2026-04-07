def test_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        auth.login(self.request, self.user)
        self.assertEqual(self.request.session[auth.SESSION_KEY], str(self.user.pk))