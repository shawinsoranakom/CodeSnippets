def test_formatting(self):
        """
        Use 'date_format' and 'time_format' to change the way a value is
        displayed.
        """
        widget = SplitDateTimeWidget(
            date_format="%d/%m/%Y",
            time_format="%H:%M",
        )
        self.check_html(
            widget,
            "date",
            datetime(2006, 1, 10, 7, 30),
            html=(
                '<input type="text" name="date_0" value="10/01/2006">'
                '<input type="text" name="date_1" value="07:30">'
            ),
        )
        self.check_html(
            widget,
            "date",
            datetime(2006, 1, 10, 7, 30),
            html=(
                '<input type="text" name="date_0" value="10/01/2006">'
                '<input type="text" name="date_1" value="07:30">'
            ),
        )