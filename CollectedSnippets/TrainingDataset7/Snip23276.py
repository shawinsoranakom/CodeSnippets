def test_render_attrs_multiple(self):
        self.check_html(
            self.widget,
            "email",
            ["test@example.com", "foo@example.com"],
            attrs={"class": "fun"},
            html=(
                '<input type="hidden" name="email" value="test@example.com" '
                'class="fun">\n'
                '<input type="hidden" name="email" value="foo@example.com" class="fun">'
            ),
        )