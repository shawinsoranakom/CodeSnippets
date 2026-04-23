def test_value_omitted_from_data(self):
        self.assertIs(
            self.widget.value_omitted_from_data({"field": "value"}, {}, "field"), False
        )
        self.assertIs(self.widget.value_omitted_from_data({}, {}, "field"), False)