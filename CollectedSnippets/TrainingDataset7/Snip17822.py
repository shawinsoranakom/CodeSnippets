def test_unusable_password(self):
        user = User.objects.create_user("testuser", "test@example.com", "test")
        data = {"email": "test@example.com"}
        form = PasswordResetForm(data)
        self.assertTrue(form.is_valid())
        user.set_unusable_password()
        user.save()
        form = PasswordResetForm(data)
        # The form itself is valid, but no email is sent
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(mail.outbox), 0)