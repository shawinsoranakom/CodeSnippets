def test_aggregate_transform(self):
        vals = Store.objects.aggregate(min_month=Min("original_opening__month"))
        self.assertEqual(vals, {"min_month": 3})