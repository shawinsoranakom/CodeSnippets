def test_filtered_aggregate_ref_subquery_annotation(self):
        aggs = Author.objects.annotate(
            earliest_book_year=Subquery(
                Book.objects.filter(
                    contact__pk=OuterRef("pk"),
                )
                .order_by("pubdate")
                .values("pubdate__year")[:1]
            ),
        ).aggregate(
            cnt=Count("pk", filter=Q(earliest_book_year=2008)),
        )
        self.assertEqual(aggs["cnt"], 2)