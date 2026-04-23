def test_distinct_ordered_sliced_subquery_aggregation(self):
        self.assertEqual(
            Tag.objects.distinct().order_by("category__name")[:3].count(), 3
        )