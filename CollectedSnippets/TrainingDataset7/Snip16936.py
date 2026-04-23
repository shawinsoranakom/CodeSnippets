def test_aggregate_join_transform(self):
        vals = Publisher.objects.aggregate(min_year=Min("book__pubdate__year"))
        self.assertEqual(vals, {"min_year": 1991})