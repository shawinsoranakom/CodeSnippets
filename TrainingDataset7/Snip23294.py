def test_value_omitted_from_data(self):
        widget = MyMultiWidget(widgets=(TextInput(), TextInput()))
        self.assertIs(widget.value_omitted_from_data({}, {}, "field"), True)
        self.assertIs(
            widget.value_omitted_from_data({"field_0": "x"}, {}, "field"), False
        )
        self.assertIs(
            widget.value_omitted_from_data({"field_1": "y"}, {}, "field"), False
        )
        self.assertIs(
            widget.value_omitted_from_data(
                {"field_0": "x", "field_1": "y"}, {}, "field"
            ),
            False,
        )