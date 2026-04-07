def test_save_html_email_template_name(self):
        """
        Test the PasswordResetForm.save() method with html_email_template_name
        parameter specified.
        Test to ensure that a multipart email is sent with both text/plain
        and text/html parts.
        """
        user, username, email = self.create_dummy_user()
        form = PasswordResetForm({"email": email})
        self.assertTrue(form.is_valid())
        form.save(
            html_email_template_name="registration/html_password_reset_email.html"
        )
        msg = self.assertEmailMessageSent()
        self.assertEqual(len(msg.alternatives), 1)
        message = msg.message()
        self.assertEqual(message.get("subject"), "Custom password reset on example.com")
        self.assertEqual(len(message.get_payload()), 2)
        self.assertTrue(message.is_multipart())
        self.assertEqual(message.get_payload(0).get_content_type(), "text/plain")
        self.assertEqual(message.get_payload(1).get_content_type(), "text/html")
        self.assertEqual(message.get_all("to"), [email])
        self.assertTrue(
            re.match(
                r"^http://example.com/reset/[\w/-]+",
                message.get_payload(0).get_content(),
            )
        )
        self.assertTrue(
            re.match(
                r'^<html><a href="http://example.com/reset/[\w/-]+/">Link</a></html>$',
                message.get_payload(1).get_content(),
            )
        )