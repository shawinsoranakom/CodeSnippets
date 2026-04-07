def test_render_false(self):
        self.check_html(
            self.widget, "is_cool", False, html='<input type="checkbox" name="is_cool">'
        )