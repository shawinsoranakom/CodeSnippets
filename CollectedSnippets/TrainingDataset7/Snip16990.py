def test_aggregation_subquery_annotation_exists(self):
        latest_book_pubdate_qs = (
            Book.objects.filter(publisher=OuterRef("pk"))
            .order_by("-pubdate")
            .values("pubdate")[:1]
        )
        publisher_qs = Publisher.objects.annotate(
            latest_book_pubdate=Subquery(latest_book_pubdate_qs),
            count=Count("book"),
        )
        self.assertTrue(publisher_qs.exists())