def test_iso_8601(self):
        test_values = (
            ("P4Y", None),
            ("P4M", None),
            ("P4W", timedelta(weeks=4)),
            ("P0.5W", timedelta(weeks=0.5)),
            ("P0,5W", timedelta(weeks=0.5)),
            ("-P0.5W", timedelta(weeks=-0.5)),
            ("P1W1D", timedelta(weeks=1, days=1)),
            ("P4D", timedelta(days=4)),
            ("-P1D", timedelta(days=-1)),
            ("P0.5D", timedelta(hours=12)),
            ("P0,5D", timedelta(hours=12)),
            ("-P0.5D", timedelta(hours=-12)),
            ("-P0,5D", timedelta(hours=-12)),
            ("PT5H", timedelta(hours=5)),
            ("-PT5H", timedelta(hours=-5)),
            ("PT5M", timedelta(minutes=5)),
            ("-PT5M", timedelta(minutes=-5)),
            ("PT5S", timedelta(seconds=5)),
            ("-PT5S", timedelta(seconds=-5)),
            ("PT0.000005S", timedelta(microseconds=5)),
            ("PT0,000005S", timedelta(microseconds=5)),
            ("-PT0.000005S", timedelta(microseconds=-5)),
            ("-PT0,000005S", timedelta(microseconds=-5)),
            ("-P4DT1H", timedelta(days=-4, hours=-1)),
            # Invalid separators for decimal fractions.
            ("P3(3D", None),
            ("PT3)3H", None),
            ("PT3|3M", None),
            ("PT3/3S", None),
        )
        for source, expected in test_values:
            with self.subTest(source=source):
                self.assertEqual(parse_duration(source), expected)