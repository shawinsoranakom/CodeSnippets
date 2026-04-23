def test_far_expiration(self):
        """Cookie will expire when a distant expiration time is provided."""
        response = HttpResponse()
        future_datetime = datetime(date.today().year + 2, 1, 1, 4, 5, 6, tzinfo=UTC)
        response.set_cookie("datetime", expires=future_datetime)
        datetime_cookie = response.cookies["datetime"]
        self.assertIn(
            datetime_cookie["expires"],
            # assertIn accounts for slight time dependency (#23450)
            (
                format_datetime_rfc5322(future_datetime, usegmt=True),
                format_datetime_rfc5322(future_datetime.replace(second=7), usegmt=True),
            ),
        )