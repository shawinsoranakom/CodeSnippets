def test_render_multiple(self):
        self.check_html(
            self.widget,
            "email",
            ["test@example.com", "foo@example.com"],
            html=(
                '<input type="hidden" name="email" value="test@example.com">\n'
                '<input type="hidden" name="email" value="foo@example.com">'
            ),
        )