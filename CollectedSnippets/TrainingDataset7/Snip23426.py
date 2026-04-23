def test_l10n(self):
        t = time(12, 51, 34, 482548)
        self.check_html(
            self.widget,
            "time",
            t,
            html='<input type="text" name="time" value="12:51:34">',
        )