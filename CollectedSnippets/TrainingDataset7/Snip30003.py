def test_range_widget_render_tuple_value(self):
        field = pg_forms.ranges.DateTimeRangeField()
        dt_range_tuple = (
            datetime.datetime(2022, 4, 22, 10, 24),
            datetime.datetime(2022, 5, 12, 9, 25),
        )
        self.assertHTMLEqual(
            field.widget.render("datetimerange", dt_range_tuple),
            '<input type="text" name="datetimerange_0" value="2022-04-22 10:24:00">'
            '<input type="text" name="datetimerange_1" value="2022-05-12 09:25:00">',
        )