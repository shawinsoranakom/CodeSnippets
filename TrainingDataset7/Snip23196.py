def test_render_true(self):
        self.check_html(
            self.widget,
            "is_cool",
            True,
            html='<input checked type="checkbox" name="is_cool">',
        )