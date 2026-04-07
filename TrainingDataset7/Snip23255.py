def test_l10n(self):
        self.check_html(
            self.widget,
            "date",
            date(2007, 9, 17),
            html='<input type="text" name="date" value="17.09.2007">',
        )