def test_hours_minutes_seconds(self):
        self.assertEqual(
            parse_duration("10:15:30"), timedelta(hours=10, minutes=15, seconds=30)
        )
        self.assertEqual(
            parse_duration("1:15:30"), timedelta(hours=1, minutes=15, seconds=30)
        )
        self.assertEqual(
            parse_duration("100:200:300"),
            timedelta(hours=100, minutes=200, seconds=300),
        )