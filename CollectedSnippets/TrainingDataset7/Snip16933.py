def test_aggregate_multi_join(self):
        vals = Store.objects.aggregate(Max("books__authors__age"))
        self.assertEqual(vals, {"books__authors__age__max": 57})

        vals = Author.objects.aggregate(Min("book__publisher__num_awards"))
        self.assertEqual(vals, {"book__publisher__num_awards__min": 1})