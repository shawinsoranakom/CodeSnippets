def test_render_none(self):
        self.check_html(
            self.widget, "time", None, html='<input type="text" name="time">'
        )