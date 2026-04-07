def test_days(self):
        self.assertEqual(
            parse_duration("4 15:30"), timedelta(days=4, minutes=15, seconds=30)
        )
        self.assertEqual(
            parse_duration("4 10:15:30"),
            timedelta(days=4, hours=10, minutes=15, seconds=30),
        )