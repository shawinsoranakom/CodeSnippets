def test_message_is_python_email_message(self):
        """
        EmailMessage.message() docs: "returns a Python
        email.message.EmailMessage object."
        """
        email = EmailMessage()
        message = email.message()
        self.assertIsInstance(message, PyMessage)
        self.assertEqual(message.policy, policy.default)