def test_inherited_fields_aggregation(self):
        # Regression for 10666 - inherited fields work with annotations and
        # aggregations
        self.assertEqual(
            HardbackBook.objects.aggregate(n_pages=Sum("book_ptr__pages")),
            {"n_pages": 2078},
        )

        self.assertEqual(
            HardbackBook.objects.aggregate(n_pages=Sum("pages")),
            {"n_pages": 2078},
        )

        qs = (
            HardbackBook.objects.annotate(
                n_authors=Count("book_ptr__authors"),
            )
            .values("name", "n_authors")
            .order_by("name")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"n_authors": 2, "name": "Artificial Intelligence: A Modern Approach"},
                {
                    "n_authors": 1,
                    "name": (
                        "Paradigms of Artificial Intelligence Programming: Case "
                        "Studies in Common Lisp"
                    ),
                },
            ],
        )

        qs = (
            HardbackBook.objects.annotate(n_authors=Count("authors"))
            .values("name", "n_authors")
            .order_by("name")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"n_authors": 2, "name": "Artificial Intelligence: A Modern Approach"},
                {
                    "n_authors": 1,
                    "name": (
                        "Paradigms of Artificial Intelligence Programming: Case "
                        "Studies in Common Lisp"
                    ),
                },
            ],
        )