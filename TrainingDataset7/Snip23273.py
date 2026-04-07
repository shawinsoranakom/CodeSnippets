def test_render_single(self):
        self.check_html(
            self.widget,
            "email",
            ["test@example.com"],
            html='<input type="hidden" name="email" value="test@example.com">',
        )