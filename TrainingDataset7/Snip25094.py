def test_localized_input_func(self):
        tests = (
            (True, "True"),
            (datetime.date(1, 1, 1), "0001-01-01"),
            (datetime.datetime(1, 1, 1), "0001-01-01 00:00:00"),
        )
        with self.settings(USE_THOUSAND_SEPARATOR=True):
            for value, expected in tests:
                with self.subTest(value=value):
                    self.assertEqual(localize_input(value), expected)