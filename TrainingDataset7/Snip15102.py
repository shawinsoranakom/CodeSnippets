def test_bounded_params(self):
        tests = (
            ({"year": 2017}, datetime(2017, 1, 1), datetime(2018, 1, 1)),
            ({"year": 2017, "month": 2}, datetime(2017, 2, 1), datetime(2017, 3, 1)),
            ({"year": 2017, "month": 12}, datetime(2017, 12, 1), datetime(2018, 1, 1)),
            (
                {"year": 2017, "month": 12, "day": 15},
                datetime(2017, 12, 15),
                datetime(2017, 12, 16),
            ),
            (
                {"year": 2017, "month": 12, "day": 31},
                datetime(2017, 12, 31),
                datetime(2018, 1, 1),
            ),
            (
                {"year": 2017, "month": 2, "day": 28},
                datetime(2017, 2, 28),
                datetime(2017, 3, 1),
            ),
        )
        for query, expected_from_date, expected_to_date in tests:
            with self.subTest(query=query):
                self.assertDateParams(query, expected_from_date, expected_to_date)