def test_annotation_filter_with_subquery(self):
        long_books_qs = (
            Book.objects.filter(
                publisher=OuterRef("pk"),
                pages__gt=400,
            )
            .values("publisher")
            .annotate(count=Count("pk"))
            .values("count")
        )[:1]
        publisher_books_qs = (
            Publisher.objects.annotate(
                total_books=Count("book"),
            )
            .filter(
                total_books=Subquery(long_books_qs, output_field=IntegerField()),
            )
            .values("name")
        )
        self.assertCountEqual(
            publisher_books_qs, [{"name": "Sams"}, {"name": "Morgan Kaufmann"}]
        )