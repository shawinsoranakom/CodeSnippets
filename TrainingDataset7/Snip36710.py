def test_leap_year(self):
        start_date = datetime.date(2016, 12, 25)
        self.assertEqual(timeuntil(start_date + self.oneweek, start_date), "1\xa0week")
        self.assertEqual(timesince(start_date, start_date + self.oneweek), "1\xa0week")