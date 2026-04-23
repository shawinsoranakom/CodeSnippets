def test_annotate_ordering(self):
        books = (
            Book.objects.values("rating")
            .annotate(oldest=Max("authors__age"))
            .order_by("oldest", "rating")
        )
        self.assertEqual(
            list(books),
            [
                {"rating": 4.5, "oldest": 35},
                {"rating": 3.0, "oldest": 45},
                {"rating": 4.0, "oldest": 57},
                {"rating": 5.0, "oldest": 57},
            ],
        )

        books = (
            Book.objects.values("rating")
            .annotate(oldest=Max("authors__age"))
            .order_by("-oldest", "-rating")
        )
        self.assertEqual(
            list(books),
            [
                {"rating": 5.0, "oldest": 57},
                {"rating": 4.0, "oldest": 57},
                {"rating": 3.0, "oldest": 45},
                {"rating": 4.5, "oldest": 35},
            ],
        )