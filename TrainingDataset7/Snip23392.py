def test_constructor_attrs(self):
        widget = SplitDateTimeWidget(attrs={"class": "pretty"})
        self.check_html(
            widget,
            "date",
            datetime(2006, 1, 10, 7, 30),
            html=(
                '<input type="text" class="pretty" value="2006-01-10" name="date_0">'
                '<input type="text" class="pretty" value="07:30:00" name="date_1">'
            ),
        )