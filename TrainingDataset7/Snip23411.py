def test_render_none(self):
        self.check_html(
            self.widget, "email", None, html='<input type="text" name="email">'
        )