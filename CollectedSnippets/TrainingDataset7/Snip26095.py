def test_datetime_in_date_header(self):
        """
        A datetime in headers should be passed through to Python email intact,
        so that it uses the email header date format.
        """
        email = EmailMessage(
            headers={"Date": datetime(2001, 11, 9, 1, 8, 47, tzinfo=timezone.utc)},
        )
        message = email.message()
        self.assertEqual(message["Date"], "Fri, 09 Nov 2001 01:08:47 +0000")
        # Not the default ISO format from force_str(strings_only=False).
        self.assertNotEqual(message["Date"], "2001-11-09 01:08:47+00:00")