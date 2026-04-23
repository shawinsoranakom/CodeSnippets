def test_filtered_aggregrate_ref_in_subquery_annotation(self):
        aggs = (
            Author.objects.annotate(
                count=Subquery(
                    Book.objects.annotate(
                        weird_count=Count(
                            "pk",
                            filter=Q(pages=OuterRef("age")),
                        )
                    ).values("weird_count")[:1]
                ),
            )
            .order_by("pk")
            .aggregate(sum=Sum("count"))
        )
        self.assertEqual(aggs["sum"], 0)