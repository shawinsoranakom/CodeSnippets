def test_aggregation_exists_annotation(self):
        published_books = Book.objects.filter(publisher=OuterRef("pk"))
        publisher_qs = Publisher.objects.annotate(
            published_book=Exists(published_books),
            count=Count("book"),
        ).values_list("name", flat=True)
        self.assertCountEqual(
            list(publisher_qs),
            [
                "Apress",
                "Morgan Kaufmann",
                "Jonno's House of Books",
                "Prentice Hall",
                "Sams",
            ],
        )