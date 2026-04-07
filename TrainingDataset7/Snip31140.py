def test_fields(self):
        self.generate()
        v = Thing.objects.get(pk="a")
        self.assertEqual(v.join, "b")
        self.assertEqual(v.where, datetime.date(year=2005, month=1, day=1))