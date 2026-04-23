def test_twelve_hour_format(self):
        tests = [
            (0, "12", "12"),
            (1, "1", "01"),
            (11, "11", "11"),
            (12, "12", "12"),
            (13, "1", "01"),
            (23, "11", "11"),
        ]
        for hour, g_expected, h_expected in tests:
            dt = datetime(2000, 1, 1, hour)
            with self.subTest(hour=hour):
                self.assertEqual(dateformat.format(dt, "g"), g_expected)
                self.assertEqual(dateformat.format(dt, "h"), h_expected)