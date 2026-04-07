def test_annotation(self):
        vals = Author.objects.filter(pk=self.a1.pk).aggregate(Count("friends__id"))
        self.assertEqual(vals, {"friends__id__count": 2})

        books = (
            Book.objects.annotate(num_authors=Count("authors__name"))
            .filter(num_authors__exact=2)
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            books,
            [
                "The Definitive Guide to Django: Web Development Done Right",
                "Artificial Intelligence: A Modern Approach",
            ],
            lambda b: b.name,
        )

        authors = (
            Author.objects.annotate(num_friends=Count("friends__id", distinct=True))
            .filter(num_friends=0)
            .order_by("pk")
        )
        self.assertQuerySetEqual(authors, ["Brad Dayley"], lambda a: a.name)

        publishers = (
            Publisher.objects.annotate(num_books=Count("book__id"))
            .filter(num_books__gt=1)
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            publishers, ["Apress", "Prentice Hall"], lambda p: p.name
        )

        publishers = (
            Publisher.objects.filter(book__price__lt=Decimal("40.0"))
            .annotate(num_books=Count("book__id"))
            .filter(num_books__gt=1)
        )
        self.assertQuerySetEqual(publishers, ["Apress"], lambda p: p.name)

        books = Book.objects.annotate(num_authors=Count("authors__id")).filter(
            authors__name__contains="Norvig", num_authors__gt=1
        )
        self.assertQuerySetEqual(
            books, ["Artificial Intelligence: A Modern Approach"], lambda b: b.name
        )