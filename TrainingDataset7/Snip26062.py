def test_bad_header_error(self):
        """
        Existing code that catches deprecated BadHeaderError should be
        compatible with modern email (which raises ValueError instead).
        """
        from django.core.mail import BadHeaderError

        with self.assertRaises(BadHeaderError):
            EmailMessage(subject="Bad\r\nHeader").message()