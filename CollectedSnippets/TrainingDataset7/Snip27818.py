def test_datefield_cleans_date(self):
        f = models.DateField()
        self.assertEqual(datetime.date(2008, 10, 10), f.clean("2008-10-10", None))