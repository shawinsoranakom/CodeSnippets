def test_render_formatted(self):
        """
        Use 'format' to change the way a value is displayed.
        """
        widget = DateTimeInput(
            format="%d/%m/%Y %H:%M",
            attrs={"type": "datetime"},
        )
        d = datetime(2007, 9, 17, 12, 51, 34, 482548)
        self.check_html(
            widget,
            "date",
            d,
            html='<input type="datetime" name="date" value="17/09/2007 12:51">',
        )