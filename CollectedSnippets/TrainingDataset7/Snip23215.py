def test_value_omitted_from_data(self):
        widget = self.widget(choices=self.beatles)
        self.assertIs(widget.value_omitted_from_data({}, {}, "field"), False)
        self.assertIs(
            widget.value_omitted_from_data({"field": "value"}, {}, "field"), False
        )