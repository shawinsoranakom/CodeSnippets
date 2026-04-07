def test_render_value(self):
        """
        The microseconds are trimmed on display, by default.
        """
        d = datetime(2007, 9, 17, 12, 51, 34, 482548)
        self.assertEqual(str(d), "2007-09-17 12:51:34.482548")
        self.check_html(
            self.widget,
            "date",
            d,
            html=('<input type="text" name="date" value="2007-09-17 12:51:34">'),
        )
        self.check_html(
            self.widget,
            "date",
            datetime(2007, 9, 17, 12, 51, 34),
            html=('<input type="text" name="date" value="2007-09-17 12:51:34">'),
        )
        self.check_html(
            self.widget,
            "date",
            datetime(2007, 9, 17, 12, 51),
            html=('<input type="text" name="date" value="2007-09-17 12:51:00">'),
        )