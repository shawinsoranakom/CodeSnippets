def test_date_objects(self):
        """
        Both timesince and timeuntil should work on date objects (#17937).
        """
        today = datetime.date.today()
        self.assertEqual(timesince(today + self.oneday), "0\xa0minutes")
        self.assertEqual(timeuntil(today - self.oneday), "0\xa0minutes")