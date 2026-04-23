def test_annotation_exists_aggregate_values_chaining(self):
        qs = (
            Book.objects.values("publisher")
            .annotate(
                has_authors=Exists(
                    Book.authors.through.objects.filter(book=OuterRef("pk"))
                ),
                max_pubdate=Max("pubdate"),
            )
            .values_list("max_pubdate", flat=True)
            .order_by("max_pubdate")
        )
        self.assertCountEqual(
            qs,
            [
                datetime.date(1991, 10, 15),
                datetime.date(2008, 3, 3),
                datetime.date(2008, 6, 23),
                datetime.date(2008, 11, 3),
            ],
        )