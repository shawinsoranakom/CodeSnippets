def test_render_attrs(self):
        self.check_html(
            self.widget,
            "email",
            ["test@example.com"],
            attrs={"class": "fun"},
            html=(
                '<input type="hidden" name="email" value="test@example.com" '
                'class="fun">'
            ),
        )