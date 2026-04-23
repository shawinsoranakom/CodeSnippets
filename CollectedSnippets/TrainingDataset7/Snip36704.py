def test_display_first_unit(self):
        """
        If the two differing units aren't adjacent, only the first unit is
        displayed.
        """
        self.assertEqual(
            timesince(
                self.t,
                self.t + 2 * self.oneweek + 3 * self.onehour + 4 * self.oneminute,
            ),
            "2\xa0weeks",
        )
        self.assertEqual(
            timesince(self.t, self.t + 4 * self.oneday + 5 * self.oneminute),
            "4\xa0days",
        )