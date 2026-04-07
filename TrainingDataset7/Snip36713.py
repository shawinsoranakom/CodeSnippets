def test_thousand_years_ago(self):
        t = self.t.replace(year=self.t.year - 1000)
        self.assertEqual(timesince(t, self.t), "1000\xa0years")
        self.assertEqual(timeuntil(self.t, t), "1000\xa0years")