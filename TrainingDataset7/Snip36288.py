def test_microseconds(self):
        duration = datetime.timedelta(hours=1, minutes=3, seconds=5, microseconds=12345)
        self.assertEqual(parse_duration(duration_iso_string(duration)), duration)