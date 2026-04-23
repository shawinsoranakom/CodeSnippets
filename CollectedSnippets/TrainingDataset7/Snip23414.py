def test_render_quoted(self):
        self.check_html(
            self.widget,
            "email",
            'some "quoted" & ampersanded value',
            html=(
                '<input type="text" name="email" '
                'value="some &quot;quoted&quot; &amp; ampersanded value">'
            ),
        )