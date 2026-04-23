def test_month_filter(self):
        self.generate()
        self.assertEqual(Thing.objects.filter(where__month=1)[0].when, "a")