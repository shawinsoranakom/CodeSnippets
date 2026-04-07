def test_explicit_date(self):
        self.assertEqual(
            timesince_filter(datetime(2005, 12, 29), datetime(2005, 12, 30)), "1\xa0day"
        )