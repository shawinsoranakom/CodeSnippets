def test_render_ignore_value(self):
        self.check_html(
            self.widget,
            "password",
            "secret",
            html='<input type="password" name="password">',
        )