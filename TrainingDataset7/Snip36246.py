def test_seconds(self):
        self.assertEqual(parse_duration("30"), timedelta(seconds=30))