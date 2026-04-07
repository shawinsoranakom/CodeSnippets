def test_no_trailing_newline_in_attrs(self):
        self.check_html(
            Input(),
            "name",
            "value",
            strict=True,
            html='<input type="None" name="name" value="value">',
        )