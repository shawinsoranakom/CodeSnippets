def test_parse_postgresql_format(self):
        test_values = (
            ("1 day", timedelta(1)),
            ("-1 day", timedelta(-1)),
            ("1 day 0:00:01", timedelta(days=1, seconds=1)),
            ("1 day -0:00:01", timedelta(days=1, seconds=-1)),
            ("-1 day -0:00:01", timedelta(days=-1, seconds=-1)),
            ("-1 day +0:00:01", timedelta(days=-1, seconds=1)),
            (
                "4 days 0:15:30.1",
                timedelta(days=4, minutes=15, seconds=30, milliseconds=100),
            ),
            (
                "4 days 0:15:30.0001",
                timedelta(days=4, minutes=15, seconds=30, microseconds=100),
            ),
            ("-4 days -15:00:30", timedelta(days=-4, hours=-15, seconds=-30)),
        )
        for source, expected in test_values:
            with self.subTest(source=source):
                self.assertEqual(parse_duration(source), expected)