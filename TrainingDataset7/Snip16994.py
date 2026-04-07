def test_aggregation_subquery_annotation_values_collision(self):
        books_rating_qs = Book.objects.filter(
            pk=OuterRef("book"),
        ).values("rating")
        publisher_qs = (
            Publisher.objects.filter(
                book__contact__age__gt=20,
            )
            .annotate(
                rating=Subquery(books_rating_qs),
            )
            .values("rating")
            .annotate(total_count=Count("*"))
            .order_by("rating")
        )
        self.assertEqual(
            list(publisher_qs),
            [
                {"rating": 3.0, "total_count": 1},
                {"rating": 4.0, "total_count": 3},
                {"rating": 4.5, "total_count": 1},
                {"rating": 5.0, "total_count": 1},
            ],
        )