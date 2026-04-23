def test_parse_python_format(self):
        timedeltas = [
            timedelta(
                days=4, minutes=15, seconds=30, milliseconds=100
            ),  # fractions of seconds
            timedelta(hours=10, minutes=15, seconds=30),  # hours, minutes, seconds
            timedelta(days=4, minutes=15, seconds=30),  # multiple days
            timedelta(days=1, minutes=00, seconds=00),  # single day
            timedelta(days=-4, minutes=15, seconds=30),  # negative durations
            timedelta(minutes=15, seconds=30),  # minute & seconds
            timedelta(seconds=30),  # seconds
        ]
        for delta in timedeltas:
            with self.subTest(delta=delta):
                self.assertEqual(parse_duration(format(delta)), delta)