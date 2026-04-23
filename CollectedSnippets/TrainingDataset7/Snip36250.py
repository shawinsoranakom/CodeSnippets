def test_fractions_of_seconds(self):
        test_values = (
            ("15:30.1", timedelta(minutes=15, seconds=30, milliseconds=100)),
            ("15:30.01", timedelta(minutes=15, seconds=30, milliseconds=10)),
            ("15:30.001", timedelta(minutes=15, seconds=30, milliseconds=1)),
            ("15:30.0001", timedelta(minutes=15, seconds=30, microseconds=100)),
            ("15:30.00001", timedelta(minutes=15, seconds=30, microseconds=10)),
            ("15:30.000001", timedelta(minutes=15, seconds=30, microseconds=1)),
            ("15:30,000001", timedelta(minutes=15, seconds=30, microseconds=1)),
        )
        for source, expected in test_values:
            with self.subTest(source=source):
                self.assertEqual(parse_duration(source), expected)