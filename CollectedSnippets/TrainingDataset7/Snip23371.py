def test_custom_input_format(self):
        w = SelectDateWidget(years=("0001", "1899", "2009", "2010"))
        with translation.override(None):
            for values, expected_value in (
                (("0001", "8", "13"), "13.08.0001"),
                (("1899", "7", "11"), "11.07.1899"),
                (("2009", "3", "7"), "07.03.2009"),
            ):
                with self.subTest(values=values):
                    data = {
                        "field_%s" % field: value
                        for field, value in zip(("year", "month", "day"), values)
                    }
                    self.assertEqual(
                        w.value_from_datadict(data, {}, "field"), expected_value
                    )
                    expected_dict = {
                        field: int(value)
                        for field, value in zip(("year", "month", "day"), values)
                    }
                    self.assertEqual(w.format_value(expected_value), expected_dict)