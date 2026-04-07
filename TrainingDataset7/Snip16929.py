def test_single_aggregate(self):
        vals = Author.objects.aggregate(Avg("age"))
        self.assertEqual(vals, {"age__avg": Approximate(37.4, places=1)})