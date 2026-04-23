def test_S_format(self):
        for expected, days in [
            ("st", [1, 21, 31]),
            ("nd", [2, 22]),
            ("rd", [3, 23]),
            ("th", (n for n in range(4, 31) if n not in [21, 22, 23])),
        ]:
            for day in days:
                dt = date(1970, 1, day)
                with self.subTest(day=day):
                    self.assertEqual(dateformat.format(dt, "S"), expected)