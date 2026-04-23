def test_negative(self):
        duration = datetime.timedelta(days=-1, hours=1, minutes=3, seconds=5)
        self.assertEqual(
            parse_duration(duration_iso_string(duration)).total_seconds(),
            duration.total_seconds(),
        )