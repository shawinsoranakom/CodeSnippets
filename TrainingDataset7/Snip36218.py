def test_datetime_with_tzinfo(self):
        tz = get_fixed_timezone(-510)
        ltz = get_default_timezone()
        dt = make_aware(datetime(2009, 5, 16, 5, 30, 30), ltz)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, "U")), tz), dt)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, "U")), ltz), dt)
        # astimezone() is safe here because the target timezone doesn't have
        # DST
        self.assertEqual(
            datetime.fromtimestamp(int(format(dt, "U"))),
            dt.astimezone(ltz).replace(tzinfo=None),
        )
        self.assertEqual(
            datetime.fromtimestamp(int(format(dt, "U")), tz).timetuple(),
            dt.astimezone(tz).timetuple(),
        )
        self.assertEqual(
            datetime.fromtimestamp(int(format(dt, "U")), ltz).timetuple(),
            dt.astimezone(ltz).timetuple(),
        )