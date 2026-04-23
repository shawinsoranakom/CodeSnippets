def test_day_of_year_leap(self):
        self.assertEqual(dateformat.format(datetime(2000, 12, 31), "z"), "366")