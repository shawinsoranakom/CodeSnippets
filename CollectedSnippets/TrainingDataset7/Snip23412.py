def test_render_value(self):
        self.check_html(
            self.widget,
            "email",
            "test@example.com",
            html=('<input type="text" name="email" value="test@example.com">'),
        )