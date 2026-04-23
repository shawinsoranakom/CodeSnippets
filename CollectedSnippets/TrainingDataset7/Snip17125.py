def test_annotation_disjunction(self):
        qs = (
            Book.objects.annotate(n_authors=Count("authors"))
            .filter(Q(n_authors=2) | Q(name="Python Web Development with Django"))
            .order_by("name")
        )
        self.assertQuerySetEqual(
            qs,
            [
                "Artificial Intelligence: A Modern Approach",
                "Python Web Development with Django",
                "The Definitive Guide to Django: Web Development Done Right",
            ],
            attrgetter("name"),
        )

        qs = (
            Book.objects.annotate(n_authors=Count("authors")).filter(
                Q(name="The Definitive Guide to Django: Web Development Done Right")
                | (
                    Q(name="Artificial Intelligence: A Modern Approach")
                    & Q(n_authors=3)
                )
            )
        ).order_by("name")
        self.assertQuerySetEqual(
            qs,
            [
                "The Definitive Guide to Django: Web Development Done Right",
            ],
            attrgetter("name"),
        )

        qs = (
            Publisher.objects.annotate(
                rating_sum=Sum("book__rating"), book_count=Count("book")
            )
            .filter(Q(rating_sum__gt=5.5) | Q(rating_sum__isnull=True))
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            qs,
            [
                "Apress",
                "Prentice Hall",
                "Jonno's House of Books",
            ],
            attrgetter("name"),
        )

        qs = (
            Publisher.objects.annotate(
                rating_sum=Sum("book__rating"), book_count=Count("book")
            )
            .filter(Q(rating_sum__gt=F("book_count")) | Q(rating_sum=None))
            .order_by("num_awards")
        )
        self.assertQuerySetEqual(
            qs,
            [
                "Jonno's House of Books",
                "Sams",
                "Apress",
                "Prentice Hall",
                "Morgan Kaufmann",
            ],
            attrgetter("name"),
        )