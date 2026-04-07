def test_render(self):
        self.check_html(
            SplitArrayWidget(forms.TextInput(), size=2),
            "array",
            None,
            """
            <input name="array_0" type="text">
            <input name="array_1" type="text">
            """,
        )