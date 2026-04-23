def test_multiple_units(self):
        """Test multiple units."""
        self.assertEqual(
            timesince(self.t, self.t + 2 * self.oneday + 6 * self.onehour),
            "2\xa0days, 6\xa0hours",
        )
        self.assertEqual(
            timesince(self.t, self.t + 2 * self.oneweek + 2 * self.oneday),
            "2\xa0weeks, 2\xa0days",
        )