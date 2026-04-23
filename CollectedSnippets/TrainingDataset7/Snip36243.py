def test_parse_datetime(self):
        valid_inputs = (
            ("2012-04-23", datetime(2012, 4, 23)),
            ("2012-04-23T09:15:00", datetime(2012, 4, 23, 9, 15)),
            ("2012-4-9 4:8:16", datetime(2012, 4, 9, 4, 8, 16)),
            (
                "2012-04-23T09:15:00Z",
                datetime(2012, 4, 23, 9, 15, 0, 0, get_fixed_timezone(0)),
            ),
            (
                "2012-4-9 4:8:16-0320",
                datetime(2012, 4, 9, 4, 8, 16, 0, get_fixed_timezone(-200)),
            ),
            (
                "2012-04-23T10:20:30.400+02:30",
                datetime(2012, 4, 23, 10, 20, 30, 400000, get_fixed_timezone(150)),
            ),
            (
                "2012-04-23T10:20:30.400+02",
                datetime(2012, 4, 23, 10, 20, 30, 400000, get_fixed_timezone(120)),
            ),
            (
                "2012-04-23T10:20:30.400-02",
                datetime(2012, 4, 23, 10, 20, 30, 400000, get_fixed_timezone(-120)),
            ),
            (
                "2012-04-23T10:20:30,400-02",
                datetime(2012, 4, 23, 10, 20, 30, 400000, get_fixed_timezone(-120)),
            ),
            (
                "2012-04-23T10:20:30.400 +0230",
                datetime(2012, 4, 23, 10, 20, 30, 400000, get_fixed_timezone(150)),
            ),
            (
                "2012-04-23T10:20:30,400 +00",
                datetime(2012, 4, 23, 10, 20, 30, 400000, get_fixed_timezone(0)),
            ),
            (
                "2012-04-23T10:20:30   -02",
                datetime(2012, 4, 23, 10, 20, 30, 0, get_fixed_timezone(-120)),
            ),
        )
        for source, expected in valid_inputs:
            with self.subTest(source=source):
                self.assertEqual(parse_datetime(source), expected)

        # Invalid inputs
        self.assertIsNone(parse_datetime("20120423091500"))
        with self.assertRaises(ValueError):
            parse_datetime("2012-04-56T09:15:90")