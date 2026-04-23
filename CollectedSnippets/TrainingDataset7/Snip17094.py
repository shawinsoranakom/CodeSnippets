def test_aggregate_fexpr(self):
        # Aggregates can be used with F() expressions
        # ... where the F() is pushed into the HAVING clause
        qs = (
            Publisher.objects.annotate(num_books=Count("book"))
            .filter(num_books__lt=F("num_awards") / 2)
            .order_by("name")
            .values("name", "num_books", "num_awards")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"num_books": 1, "name": "Morgan Kaufmann", "num_awards": 9},
                {"num_books": 2, "name": "Prentice Hall", "num_awards": 7},
            ],
        )

        qs = (
            Publisher.objects.annotate(num_books=Count("book"))
            .exclude(num_books__lt=F("num_awards") / 2)
            .order_by("name")
            .values("name", "num_books", "num_awards")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"num_books": 2, "name": "Apress", "num_awards": 3},
                {"num_books": 0, "name": "Jonno's House of Books", "num_awards": 0},
                {"num_books": 1, "name": "Sams", "num_awards": 1},
            ],
        )

        # ... and where the F() references an aggregate
        qs = (
            Publisher.objects.annotate(num_books=Count("book"))
            .filter(num_awards__gt=2 * F("num_books"))
            .order_by("name")
            .values("name", "num_books", "num_awards")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"num_books": 1, "name": "Morgan Kaufmann", "num_awards": 9},
                {"num_books": 2, "name": "Prentice Hall", "num_awards": 7},
            ],
        )

        qs = (
            Publisher.objects.annotate(num_books=Count("book"))
            .exclude(num_books__lt=F("num_awards") / 2)
            .order_by("name")
            .values("name", "num_books", "num_awards")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"num_books": 2, "name": "Apress", "num_awards": 3},
                {"num_books": 0, "name": "Jonno's House of Books", "num_awards": 0},
                {"num_books": 1, "name": "Sams", "num_awards": 1},
            ],
        )