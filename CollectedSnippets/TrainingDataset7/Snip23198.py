def test_render_int(self):
        """
        Integers are handled by value, not as booleans (#17114).
        """
        self.check_html(
            self.widget,
            "is_cool",
            0,
            html='<input checked type="checkbox" name="is_cool" value="0">',
        )
        self.check_html(
            self.widget,
            "is_cool",
            1,
            html='<input checked type="checkbox" name="is_cool" value="1">',
        )