def test_save_send_email_exceptions_are_catched_and_logged(self):
        user, username, email = self.create_dummy_user()
        form = PasswordResetForm({"email": email})
        self.assertTrue(form.is_valid())

        with self.assertLogs("django.contrib.auth", level=0) as cm:
            form.save()

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(cm.output), 1)
        errors = cm.output[0].split("\n")
        pk = user.pk
        self.assertEqual(
            errors[0],
            f"ERROR:django.contrib.auth:Failed to send password reset email to {pk}",
        )
        self.assertEqual(
            errors[-1], "ValueError: FailingEmailBackend is doomed to fail."
        )