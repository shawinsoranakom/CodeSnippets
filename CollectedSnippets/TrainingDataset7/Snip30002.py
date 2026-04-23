def test_range_widget(self):
        f = pg_forms.ranges.DateTimeRangeField()
        self.assertHTMLEqual(
            f.widget.render("datetimerange", ""),
            '<input type="text" name="datetimerange_0">'
            '<input type="text" name="datetimerange_1">',
        )
        self.assertHTMLEqual(
            f.widget.render("datetimerange", None),
            '<input type="text" name="datetimerange_0">'
            '<input type="text" name="datetimerange_1">',
        )
        dt_range = DateTimeTZRange(
            datetime.datetime(2006, 1, 10, 7, 30), datetime.datetime(2006, 2, 12, 9, 50)
        )
        self.assertHTMLEqual(
            f.widget.render("datetimerange", dt_range),
            '<input type="text" name="datetimerange_0" value="2006-01-10 07:30:00">'
            '<input type="text" name="datetimerange_1" value="2006-02-12 09:50:00">',
        )