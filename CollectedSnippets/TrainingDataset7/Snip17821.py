def test_inactive_user(self):
        """
        Inactive user cannot receive password reset email.
        """
        user, username, email = self.create_dummy_user()
        user.is_active = False
        user.save()
        form = PasswordResetForm({"email": email})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(mail.outbox), 0)