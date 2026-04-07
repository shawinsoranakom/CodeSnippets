def test_date_header_localtime(self):
        """
        EMAIL_USE_LOCALTIME=True creates a datetime in the local time zone.
        """
        email = EmailMessage()
        # Africa/Algiers is UTC+1 year round.
        self.assertEndsWith(email.message()["Date"], "+0100")