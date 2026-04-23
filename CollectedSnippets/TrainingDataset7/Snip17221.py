def test_annotation_subquery_and_aggregate_values_chaining(self):
        qs = (
            Book.objects.annotate(pub_year=ExtractYear("pubdate"))
            .values("pub_year")
            .annotate(
                top_rating=Subquery(
                    Book.objects.filter(pubdate__year=OuterRef("pub_year"))
                    .order_by("-rating")
                    .values("rating")[:1]
                ),
                total_pages=Sum("pages"),
            )
            .values("pub_year", "total_pages", "top_rating")
        )
        self.assertCountEqual(
            qs,
            [
                {"pub_year": 1991, "top_rating": 5.0, "total_pages": 946},
                {"pub_year": 1995, "top_rating": 4.0, "total_pages": 1132},
                {"pub_year": 2007, "top_rating": 4.5, "total_pages": 447},
                {"pub_year": 2008, "top_rating": 4.0, "total_pages": 1178},
            ],
        )