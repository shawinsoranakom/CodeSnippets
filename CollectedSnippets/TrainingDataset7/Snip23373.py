def test_value_from_datadict(self):
        tests = [
            (("2000", "12", "1"), "2000-12-01"),
            (("", "12", "1"), "0-12-1"),
            (("2000", "", "1"), "2000-0-1"),
            (("2000", "12", ""), "2000-12-0"),
            (("", "", "", ""), None),
            ((None, "12", "1"), None),
            (("2000", None, "1"), None),
            (("2000", "12", None), None),
            (
                (str(sys.maxsize + 1), "12", "1"),
                # PyPy does not raise OverflowError.
                f"{sys.maxsize + 1}-12-1" if PYPY else "0-0-0",
            ),
        ]
        for values, expected in tests:
            with self.subTest(values=values):
                data = {}
                for field_name, value in zip(("year", "month", "day"), values):
                    if value is not None:
                        data["field_%s" % field_name] = value
                self.assertEqual(
                    self.widget.value_from_datadict(data, {}, "field"), expected
                )