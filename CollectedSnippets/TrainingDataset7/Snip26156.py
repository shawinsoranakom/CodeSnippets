def test_all_params_optional(self):
        """
        EmailMessage class docs: "All parameters are optional"
        """
        email = EmailMessage()
        self.assertIsInstance(email.message(), PyMessage)  # force serialization.

        email = EmailMultiAlternatives()
        self.assertIsInstance(email.message(), PyMessage)