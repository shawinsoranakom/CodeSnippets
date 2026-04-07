def test_render_none(self):
        self.check_html(
            self.widget, "is_cool", None, html='<input type="checkbox" name="is_cool">'
        )