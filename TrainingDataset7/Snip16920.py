def test_filtered_aggregate_ref_multiple_subquery_annotation(self):
        aggregate = (
            Book.objects.values("publisher")
            .annotate(
                has_authors=Exists(
                    Book.authors.through.objects.filter(book=OuterRef("pk")),
                ),
                authors_have_other_books=Exists(
                    Book.objects.filter(
                        authors__in=Author.objects.filter(
                            book_contact_set=OuterRef(OuterRef("pk")),
                        )
                    ).exclude(pk=OuterRef("pk")),
                ),
            )
            .aggregate(
                max_rating=Max(
                    "rating",
                    filter=Q(has_authors=True, authors_have_other_books=False),
                )
            )
        )
        self.assertEqual(aggregate, {"max_rating": 4.5})