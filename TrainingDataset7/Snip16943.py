def test_annotate_values(self):
        books = list(
            Book.objects.filter(pk=self.b1.pk)
            .annotate(mean_age=Avg("authors__age"))
            .values()
        )
        self.assertEqual(
            books,
            [
                {
                    "contact_id": self.a1.id,
                    "id": self.b1.id,
                    "isbn": "159059725",
                    "mean_age": 34.5,
                    "name": (
                        "The Definitive Guide to Django: Web Development Done Right"
                    ),
                    "pages": 447,
                    "price": Approximate(Decimal("30")),
                    "pubdate": datetime.date(2007, 12, 6),
                    "publisher_id": self.p1.id,
                    "rating": 4.5,
                }
            ],
        )

        books = (
            Book.objects.filter(pk=self.b1.pk)
            .annotate(mean_age=Avg("authors__age"))
            .values("pk", "isbn", "mean_age")
        )
        self.assertEqual(
            list(books),
            [
                {
                    "pk": self.b1.pk,
                    "isbn": "159059725",
                    "mean_age": 34.5,
                }
            ],
        )

        books = (
            Book.objects.filter(pk=self.b1.pk)
            .annotate(mean_age=Avg("authors__age"))
            .values("name")
        )
        self.assertEqual(
            list(books),
            [{"name": "The Definitive Guide to Django: Web Development Done Right"}],
        )

        books = (
            Book.objects.filter(pk=self.b1.pk)
            .values()
            .annotate(mean_age=Avg("authors__age"))
        )
        self.assertEqual(
            list(books),
            [
                {
                    "contact_id": self.a1.id,
                    "id": self.b1.id,
                    "isbn": "159059725",
                    "mean_age": 34.5,
                    "name": (
                        "The Definitive Guide to Django: Web Development Done Right"
                    ),
                    "pages": 447,
                    "price": Approximate(Decimal("30")),
                    "pubdate": datetime.date(2007, 12, 6),
                    "publisher_id": self.p1.id,
                    "rating": 4.5,
                }
            ],
        )

        books = (
            Book.objects.values("rating")
            .annotate(n_authors=Count("authors__id"), mean_age=Avg("authors__age"))
            .order_by("rating")
        )
        self.assertEqual(
            list(books),
            [
                {
                    "rating": 3.0,
                    "n_authors": 1,
                    "mean_age": 45.0,
                },
                {
                    "rating": 4.0,
                    "n_authors": 6,
                    "mean_age": Approximate(37.16, places=1),
                },
                {
                    "rating": 4.5,
                    "n_authors": 2,
                    "mean_age": 34.5,
                },
                {
                    "rating": 5.0,
                    "n_authors": 1,
                    "mean_age": 57.0,
                },
            ],
        )

        authors = Author.objects.annotate(Avg("friends__age")).order_by("name")
        self.assertQuerySetEqual(
            authors,
            [
                ("Adrian Holovaty", 32.0),
                ("Brad Dayley", None),
                ("Jacob Kaplan-Moss", 29.5),
                ("James Bennett", 34.0),
                ("Jeffrey Forcier", 27.0),
                ("Paul Bissex", 31.0),
                ("Peter Norvig", 46.0),
                ("Stuart Russell", 57.0),
                ("Wesley J. Chun", Approximate(33.66, places=1)),
            ],
            lambda a: (a.name, a.friends__age__avg),
        )