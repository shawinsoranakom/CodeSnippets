def test_render_attrs(self):
        self.check_html(
            SplitArrayWidget(forms.TextInput(), size=2),
            "array",
            ["val1", "val2"],
            attrs={"id": "foo"},
            html=("""
                <input id="foo_0" name="array_0" type="text" value="val1">
                <input id="foo_1" name="array_1" type="text" value="val2">
                """),
        )