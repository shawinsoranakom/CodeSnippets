def test_save_plaintext_email(self):
        """
        Test the PasswordResetForm.save() method with no
        html_email_template_name parameter passed in. Test to ensure original
        behavior is unchanged after the parameter was added.
        """
        user, username, email = self.create_dummy_user()
        form = PasswordResetForm({"email": email})
        self.assertTrue(form.is_valid())
        form.save()
        msg = self.assertEmailMessageSent()
        self.assertEqual(len(msg.alternatives), 0)
        message = msg.message()
        self.assertFalse(message.is_multipart())
        self.assertEqual(message.get_content_type(), "text/plain")
        self.assertEqual(message.get("subject"), "Custom password reset on example.com")
        self.assertEqual(message.get_all("to"), [email])
        self.assertTrue(
            re.match(r"^http://example.com/reset/[\w+/-]", message.get_payload())
        )