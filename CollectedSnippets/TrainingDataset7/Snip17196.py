def test_annotation_reverse_m2m(self):
        books = (
            Book.objects.annotate(
                store_name=F("store__name"),
            )
            .filter(
                name="Practical Django Projects",
            )
            .order_by("store_name")
        )

        self.assertQuerySetEqual(
            books,
            ["Amazon.com", "Books.com", "Mamma and Pappa's Books"],
            lambda b: b.store_name,
        )