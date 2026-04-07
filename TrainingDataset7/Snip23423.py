def test_render_value(self):
        """
        The microseconds are trimmed on display, by default.
        """
        t = time(12, 51, 34, 482548)
        self.assertEqual(str(t), "12:51:34.482548")
        self.check_html(
            self.widget,
            "time",
            t,
            html='<input type="text" name="time" value="12:51:34">',
        )
        self.check_html(
            self.widget,
            "time",
            time(12, 51, 34),
            html=('<input type="text" name="time" value="12:51:34">'),
        )
        self.check_html(
            self.widget,
            "time",
            time(12, 51),
            html=('<input type="text" name="time" value="12:51:00">'),
        )