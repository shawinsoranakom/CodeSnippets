def test_empty_filtered_aggregates_with_annotation(self):
        agg = Count("pk", filter=Q())
        self.assertEqual(
            Author.objects.annotate(
                age_annotation=F("age"),
            ).aggregate(
                count=agg
            )["count"],
            3,
        )