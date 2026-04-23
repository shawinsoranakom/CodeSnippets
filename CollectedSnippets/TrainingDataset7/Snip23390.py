def test_render_datetime(self):
        self.check_html(
            self.widget,
            "date",
            datetime(2006, 1, 10, 7, 30),
            html=(
                '<input type="text" name="date_0" value="2006-01-10">'
                '<input type="text" name="date_1" value="07:30:00">'
            ),
        )