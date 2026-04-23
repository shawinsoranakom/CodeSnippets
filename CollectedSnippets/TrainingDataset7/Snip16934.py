def test_aggregate_alias(self):
        vals = Store.objects.filter(name="Amazon.com").aggregate(
            amazon_mean=Avg("books__rating")
        )
        self.assertEqual(vals, {"amazon_mean": Approximate(4.08, places=2)})