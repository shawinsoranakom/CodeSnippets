def test_render_value(self):
        d = datetime(2007, 9, 17, 12, 51, 34, 482548)
        self.check_html(
            self.widget,
            "date",
            d,
            html=(
                '<input type="hidden" name="date_0" value="2007-09-17">'
                '<input type="hidden" name="date_1" value="12:51:34">'
            ),
        )
        self.check_html(
            self.widget,
            "date",
            datetime(2007, 9, 17, 12, 51, 34),
            html=(
                '<input type="hidden" name="date_0" value="2007-09-17">'
                '<input type="hidden" name="date_1" value="12:51:34">'
            ),
        )
        self.check_html(
            self.widget,
            "date",
            datetime(2007, 9, 17, 12, 51),
            html=(
                '<input type="hidden" name="date_0" value="2007-09-17">'
                '<input type="hidden" name="date_1" value="12:51:00">'
            ),
        )