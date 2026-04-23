def test_render_custom_attrs(self):
        self.check_html(
            self.widget,
            "email",
            "test@example.com",
            attrs={"class": "fun"},
            html=(
                '<input type="text" name="email" value="test@example.com" class="fun">'
            ),
        )