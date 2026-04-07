def test_invalid_params(self):
        tests = (
            {"year": "x"},
            {"year": 2017, "month": "x"},
            {"year": 2017, "month": 12, "day": "x"},
            {"year": 2017, "month": 13},
            {"year": 2017, "month": 12, "day": 32},
            {"year": 2017, "month": 0},
            {"year": 2017, "month": 12, "day": 0},
        )
        for invalid_query in tests:
            with (
                self.subTest(query=invalid_query),
                self.assertRaises(IncorrectLookupParameters),
            ):
                self.assertDateParams(invalid_query, None, None)