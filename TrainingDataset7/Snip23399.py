def test_constructor_different_attrs(self):
        html = (
            '<input type="hidden" class="foo" value="2006-01-10" name="date_0">'
            '<input type="hidden" class="bar" value="07:30:00" name="date_1">'
        )
        widget = SplitHiddenDateTimeWidget(
            date_attrs={"class": "foo"}, time_attrs={"class": "bar"}
        )
        self.check_html(widget, "date", datetime(2006, 1, 10, 7, 30), html=html)
        widget = SplitHiddenDateTimeWidget(
            date_attrs={"class": "foo"}, attrs={"class": "bar"}
        )
        self.check_html(widget, "date", datetime(2006, 1, 10, 7, 30), html=html)
        widget = SplitHiddenDateTimeWidget(
            time_attrs={"class": "bar"}, attrs={"class": "foo"}
        )
        self.check_html(widget, "date", datetime(2006, 1, 10, 7, 30), html=html)