def test_render_empty(self):
        self.check_html(
            self.widget, "is_cool", "", html='<input type="checkbox" name="is_cool">'
        )