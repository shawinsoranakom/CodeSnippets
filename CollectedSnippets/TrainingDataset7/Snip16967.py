def test_ticket12886(self):
        """
        Aggregation over sliced queryset works correctly.
        """
        qs = Book.objects.order_by("-rating")[0:3]
        vals = qs.aggregate(average_top3_rating=Avg("rating"))["average_top3_rating"]
        self.assertAlmostEqual(vals, 4.5, places=2)