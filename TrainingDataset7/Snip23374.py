def test_value_omitted_from_data(self):
        self.assertIs(self.widget.value_omitted_from_data({}, {}, "field"), True)
        self.assertIs(
            self.widget.value_omitted_from_data({"field_month": "12"}, {}, "field"),
            False,
        )
        self.assertIs(
            self.widget.value_omitted_from_data({"field_year": "2000"}, {}, "field"),
            False,
        )
        self.assertIs(
            self.widget.value_omitted_from_data({"field_day": "1"}, {}, "field"), False
        )
        data = {"field_day": "1", "field_month": "12", "field_year": "2000"}
        self.assertIs(self.widget.value_omitted_from_data(data, {}, "field"), False)