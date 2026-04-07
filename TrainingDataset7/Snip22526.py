def test_datetimefield_clean_input_formats(self):
        tests = [
            (
                "%Y %m %d %I:%M %p",
                (
                    (date(2006, 10, 25), datetime(2006, 10, 25, 0, 0)),
                    (datetime(2006, 10, 25, 14, 30), datetime(2006, 10, 25, 14, 30)),
                    (
                        datetime(2006, 10, 25, 14, 30, 59),
                        datetime(2006, 10, 25, 14, 30, 59),
                    ),
                    (
                        datetime(2006, 10, 25, 14, 30, 59, 200),
                        datetime(2006, 10, 25, 14, 30, 59, 200),
                    ),
                    ("2006 10 25 2:30 PM", datetime(2006, 10, 25, 14, 30)),
                    # ISO-like formats are always accepted.
                    ("2006-10-25 14:30:45", datetime(2006, 10, 25, 14, 30, 45)),
                ),
            ),
            (
                "%Y.%m.%d %H:%M:%S.%f",
                (
                    (
                        "2006.10.25 14:30:45.0002",
                        datetime(2006, 10, 25, 14, 30, 45, 200),
                    ),
                ),
            ),
        ]
        for input_format, values in tests:
            f = DateTimeField(input_formats=[input_format])
            for value, expected_datetime in values:
                with self.subTest(value=value, input_format=input_format):
                    self.assertEqual(f.clean(value), expected_datetime)