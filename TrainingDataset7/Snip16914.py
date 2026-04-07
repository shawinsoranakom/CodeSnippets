def test_filtered_aggregate_on_annotate(self):
        pages_annotate = Sum("book__pages", filter=Q(book__rating__gt=3))
        age_agg = Sum("age", filter=Q(total_pages__gte=400))
        aggregated = Author.objects.annotate(total_pages=pages_annotate).aggregate(
            summed_age=age_agg
        )
        self.assertEqual(aggregated, {"summed_age": 140})