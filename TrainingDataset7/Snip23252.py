def test_render_value(self):
        d = date(2007, 9, 17)
        self.assertEqual(str(d), "2007-09-17")

        self.check_html(
            self.widget,
            "date",
            d,
            html='<input type="text" name="date" value="2007-09-17">',
        )
        self.check_html(
            self.widget,
            "date",
            date(2007, 9, 17),
            html=('<input type="text" name="date" value="2007-09-17">'),
        )