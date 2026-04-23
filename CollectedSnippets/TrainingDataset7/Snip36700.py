def test_equal_datetimes(self):
        """equal datetimes."""
        # NOTE: \xa0 avoids wrapping between value and unit
        self.assertEqual(timesince(self.t, self.t), "0\xa0minutes")