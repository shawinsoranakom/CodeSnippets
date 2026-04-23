def test_less_than_a_day_cross_day_with_zoneinfo(self):
        now_with_zoneinfo = timezone.make_aware(
            datetime.datetime(2023, 4, 14, 1, 30, 30),
            zoneinfo.ZoneInfo(key="Asia/Kathmandu"),  # UTC+05:45
        )
        now_utc = now_with_zoneinfo.astimezone(datetime.UTC)
        tests = [
            (now_with_zoneinfo, "0\xa0minutes"),
            (now_with_zoneinfo - self.onemicrosecond, "0\xa0minutes"),
            (now_with_zoneinfo - self.onesecond, "0\xa0minutes"),
            (now_with_zoneinfo - self.oneminute, "1\xa0minute"),
            (now_with_zoneinfo - self.onehour, "1\xa0hour"),
        ]
        for value, expected in tests:
            with self.subTest(value):
                self.assertEqual(timesince(value, now_utc), expected)