def test_render_none(self):
        self.check_html(
            self.widget, "date", None, html='<input type="text" name="date">'
        )