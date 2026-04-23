def test_deprecated_on_import(self):
        """
        These items are not typically called from user code,
        so generate deprecation warnings immediately at the time
        they are imported from django.core.mail.
        """
        cases = [
            # name, msg
            (
                "BadHeaderError",
                "BadHeaderError is deprecated. Replace with ValueError.",
            ),
            (
                "SafeMIMEText",
                "SafeMIMEText is deprecated. The return value of"
                " EmailMessage.message() is an email.message.EmailMessage.",
            ),
            (
                "SafeMIMEMultipart",
                "SafeMIMEMultipart is deprecated. The return value of"
                " EmailMessage.message() is an email.message.EmailMessage.",
            ),
        ]
        for name, msg in cases:
            with self.subTest(name=name):
                with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
                    __import__("django.core.mail", fromlist=[name])