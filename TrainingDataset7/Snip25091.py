def test_basque_date_formats(self):
        # Basque locale uses parenthetical suffixes for conditional declension:
        # (e)ko for years and declined month/day forms.
        with translation.override("eu", deactivate=True):
            self.assertEqual(date_format(self.d), "2009(e)ko abe.k 31")
            self.assertEqual(
                date_format(self.dt, "DATETIME_FORMAT"),
                "2009(e)ko abe.k 31, 20:50",
            )
            self.assertEqual(
                date_format(self.d, "YEAR_MONTH_FORMAT"), "2009(e)ko abendua"
            )
            self.assertEqual(date_format(self.d, "MONTH_DAY_FORMAT"), "abenduaren 31a")
            # Day 11 (hamaika in Basque) ends in 'a' as a word, but the
            # numeral form does not, so appending 'a' is correct here.
            self.assertEqual(
                date_format(datetime.date(2009, 12, 11), "MONTH_DAY_FORMAT"),
                "abenduaren 11a",
            )