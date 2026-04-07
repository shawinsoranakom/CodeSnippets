def test_minutes_seconds(self):
        self.assertEqual(parse_duration("15:30"), timedelta(minutes=15, seconds=30))
        self.assertEqual(parse_duration("5:30"), timedelta(minutes=5, seconds=30))