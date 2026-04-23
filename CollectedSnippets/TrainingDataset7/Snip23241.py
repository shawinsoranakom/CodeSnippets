def test_value_omitted_from_data(self):
        widget = ClearableFileInput()
        self.assertIs(widget.value_omitted_from_data({}, {}, "field"), True)
        self.assertIs(
            widget.value_omitted_from_data({}, {"field": "x"}, "field"), False
        )
        self.assertIs(
            widget.value_omitted_from_data({"field-clear": "y"}, {}, "field"), False
        )