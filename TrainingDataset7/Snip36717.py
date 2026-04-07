def test_less_than_a_day_with_zoneinfo(self):
        now_with_zoneinfo = timezone.now().astimezone(
            zoneinfo.ZoneInfo(key="Asia/Kathmandu")  # UTC+05:45
        )
        tests = [
            (now_with_zoneinfo, "0\xa0minutes"),
            (now_with_zoneinfo - self.onemicrosecond, "0\xa0minutes"),
            (now_with_zoneinfo - self.onesecond, "0\xa0minutes"),
            (now_with_zoneinfo - self.oneminute, "1\xa0minute"),
            (now_with_zoneinfo - self.onehour, "1\xa0hour"),
        ]
        for value, expected in tests:
            with self.subTest(value):
                self.assertEqual(timesince(value), expected)