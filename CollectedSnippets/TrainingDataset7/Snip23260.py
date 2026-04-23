def test_l10n(self):
        d = datetime(2007, 9, 17, 12, 51, 34, 482548)
        self.check_html(
            self.widget,
            "date",
            d,
            html=('<input type="text" name="date" value="17.09.2007 12:51:34">'),
        )