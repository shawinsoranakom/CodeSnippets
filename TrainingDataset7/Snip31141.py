def test_dates(self):
        self.generate()
        resp = Thing.objects.dates("where", "year")
        self.assertEqual(
            list(resp),
            [
                datetime.date(2005, 1, 1),
                datetime.date(2006, 1, 1),
            ],
        )