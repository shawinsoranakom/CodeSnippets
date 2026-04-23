def test_render_attrs_constructor(self):
        widget = MultipleHiddenInput(attrs={"class": "fun"})
        self.check_html(widget, "email", [], "")
        self.check_html(
            widget,
            "email",
            ["foo@example.com"],
            html=(
                '<input type="hidden" class="fun" value="foo@example.com" name="email">'
            ),
        )
        self.check_html(
            widget,
            "email",
            ["foo@example.com", "test@example.com"],
            html=(
                '<input type="hidden" class="fun" value="foo@example.com" '
                'name="email">\n'
                '<input type="hidden" class="fun" value="test@example.com" '
                'name="email">'
            ),
        )
        self.check_html(
            widget,
            "email",
            ["foo@example.com"],
            attrs={"class": "special"},
            html=(
                '<input type="hidden" class="special" value="foo@example.com" '
                'name="email">'
            ),
        )