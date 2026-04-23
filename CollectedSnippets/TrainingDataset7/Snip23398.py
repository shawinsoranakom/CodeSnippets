def test_l10n(self):
        d = datetime(2007, 9, 17, 12, 51)
        self.check_html(
            self.widget,
            "date",
            d,
            html=("""
            <input type="hidden" name="date_0" value="17.09.2007">
            <input type="hidden" name="date_1" value="12:51:00">
            """),
        )