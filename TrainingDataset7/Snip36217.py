def test_datetime_with_local_tzinfo(self):
        ltz = get_default_timezone()
        dt = make_aware(datetime(2009, 5, 16, 5, 30, 30), ltz)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, "U")), ltz), dt)
        self.assertEqual(
            datetime.fromtimestamp(int(format(dt, "U"))), dt.replace(tzinfo=None)
        )