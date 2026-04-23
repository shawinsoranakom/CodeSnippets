def test_date_header_utc(self):
        """
        EMAIL_USE_LOCALTIME=False creates a datetime in UTC.
        """
        email = EmailMessage()
        # Per RFC 2822/5322 section 3.3, "The form '+0000' SHOULD be used
        # to indicate a time zone at Universal Time."
        self.assertEndsWith(email.message()["Date"], "+0000")