def test_render_check_test(self):
        """
        You can pass 'check_test' to the constructor. This is a callable that
        takes the value and returns True if the box should be checked.
        """
        widget = CheckboxInput(check_test=lambda value: value.startswith("hello"))
        self.check_html(
            widget, "greeting", "", html=('<input type="checkbox" name="greeting">')
        )
        self.check_html(
            widget,
            "greeting",
            "hello",
            html=('<input checked type="checkbox" name="greeting" value="hello">'),
        )
        self.check_html(
            widget,
            "greeting",
            "hello there",
            html=(
                '<input checked type="checkbox" name="greeting" value="hello there">'
            ),
        )
        self.check_html(
            widget,
            "greeting",
            "hello & goodbye",
            html=(
                '<input checked type="checkbox" name="greeting" '
                'value="hello &amp; goodbye">'
            ),
        )