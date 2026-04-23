def test_naturalday_tz(self):
        today = datetime.date.today()
        tz_one = get_fixed_timezone(-720)
        tz_two = get_fixed_timezone(720)

        # Can be today or yesterday
        date_one = datetime.datetime(today.year, today.month, today.day, tzinfo=tz_one)
        naturalday_one = humanize.naturalday(date_one)
        # Can be today or tomorrow
        date_two = datetime.datetime(today.year, today.month, today.day, tzinfo=tz_two)
        naturalday_two = humanize.naturalday(date_two)

        # As 24h of difference they will never be the same
        self.assertNotEqual(naturalday_one, naturalday_two)