def test_render_value(self):
        """
        Using any value that's not in ('', None, False, True) will check the
        checkbox and set the 'value' attribute.
        """
        self.check_html(
            self.widget,
            "is_cool",
            "foo",
            html='<input checked type="checkbox" name="is_cool" value="foo">',
        )