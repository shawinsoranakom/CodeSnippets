def test_value_omitted_from_data(self):
        widget = SplitArrayWidget(forms.TextInput(), size=2)
        self.assertIs(widget.value_omitted_from_data({}, {}, "field"), True)
        self.assertIs(
            widget.value_omitted_from_data({"field_0": "value"}, {}, "field"), False
        )
        self.assertIs(
            widget.value_omitted_from_data({"field_1": "value"}, {}, "field"), False
        )
        self.assertIs(
            widget.value_omitted_from_data(
                {"field_0": "value", "field_1": "value"}, {}, "field"
            ),
            False,
        )