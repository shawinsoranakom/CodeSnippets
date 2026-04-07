def test_nonexistent_email(self):
        """
        Test nonexistent email address. This should not fail because it would
        expose information about registered users.
        """
        data = {"email": "foo@bar.com"}
        form = PasswordResetForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(len(mail.outbox), 0)