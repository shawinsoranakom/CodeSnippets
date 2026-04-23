def test_render_empty(self):
        self.check_html(self.widget, "email", [], "")