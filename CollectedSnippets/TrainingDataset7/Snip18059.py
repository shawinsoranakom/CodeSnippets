def test_changed_password_invalidates_session(self):
        # After password change, user should be anonymous
        self.user.set_password("new_password")
        self.user.save()
        self.middleware(self.request)
        self.assertIsNotNone(self.request.user)
        self.assertTrue(self.request.user.is_anonymous)
        # session should be flushed
        self.assertIsNone(self.request.session.session_key)