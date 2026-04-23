def test_explicit_date(self):
        self.assertEqual(
            timeuntil_filter(datetime(2005, 12, 30), datetime(2005, 12, 29)), "1\xa0day"
        )