def test_date(self):
        d = date(2009, 5, 16)
        self.assertEqual(date.fromtimestamp(int(format(d, "U"))), d)