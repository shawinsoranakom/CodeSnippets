def test_custom_email_subject(self):
        data = {"email": "testclient@example.com"}
        form = PasswordResetForm(data)
        self.assertTrue(form.is_valid())
        # Since we're not providing a request object, we must provide a
        # domain_override to prevent the save operation from failing in the
        # potential case where contrib.sites is not installed. Refs #16412.
        form.save(domain_override="example.com")
        self.assertEmailMessageSent(subject="Custom password reset on example.com")