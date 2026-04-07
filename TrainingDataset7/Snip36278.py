def test_simple(self):
        duration = datetime.timedelta(hours=1, minutes=3, seconds=5)
        self.assertEqual(parse_duration(duration_string(duration)), duration)