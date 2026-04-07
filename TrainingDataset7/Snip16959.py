def test_filtering(self):
        p = Publisher.objects.create(name="Expensive Publisher", num_awards=0)
        Book.objects.create(
            name="ExpensiveBook1",
            pages=1,
            isbn="111",
            rating=3.5,
            price=Decimal("1000"),
            publisher=p,
            contact_id=self.a1.id,
            pubdate=datetime.date(2008, 12, 1),
        )
        Book.objects.create(
            name="ExpensiveBook2",
            pages=1,
            isbn="222",
            rating=4.0,
            price=Decimal("1000"),
            publisher=p,
            contact_id=self.a1.id,
            pubdate=datetime.date(2008, 12, 2),
        )
        Book.objects.create(
            name="ExpensiveBook3",
            pages=1,
            isbn="333",
            rating=4.5,
            price=Decimal("35"),
            publisher=p,
            contact_id=self.a1.id,
            pubdate=datetime.date(2008, 12, 3),
        )

        publishers = (
            Publisher.objects.annotate(num_books=Count("book__id"))
            .filter(num_books__gt=1)
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            publishers,
            ["Apress", "Prentice Hall", "Expensive Publisher"],
            lambda p: p.name,
        )

        publishers = Publisher.objects.filter(book__price__lt=Decimal("40.0")).order_by(
            "pk"
        )
        self.assertQuerySetEqual(
            publishers,
            [
                "Apress",
                "Apress",
                "Sams",
                "Prentice Hall",
                "Expensive Publisher",
            ],
            lambda p: p.name,
        )

        publishers = (
            Publisher.objects.annotate(num_books=Count("book__id"))
            .filter(num_books__gt=1, book__price__lt=Decimal("40.0"))
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            publishers,
            ["Apress", "Prentice Hall", "Expensive Publisher"],
            lambda p: p.name,
        )

        publishers = (
            Publisher.objects.filter(book__price__lt=Decimal("40.0"))
            .annotate(num_books=Count("book__id"))
            .filter(num_books__gt=1)
            .order_by("pk")
        )
        self.assertQuerySetEqual(publishers, ["Apress"], lambda p: p.name)

        publishers = (
            Publisher.objects.annotate(num_books=Count("book"))
            .filter(num_books__range=[1, 3])
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            publishers,
            [
                "Apress",
                "Sams",
                "Prentice Hall",
                "Morgan Kaufmann",
                "Expensive Publisher",
            ],
            lambda p: p.name,
        )

        publishers = (
            Publisher.objects.annotate(num_books=Count("book"))
            .filter(num_books__range=[1, 2])
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            publishers,
            ["Apress", "Sams", "Prentice Hall", "Morgan Kaufmann"],
            lambda p: p.name,
        )

        publishers = (
            Publisher.objects.annotate(num_books=Count("book"))
            .filter(num_books__in=[1, 3])
            .order_by("pk")
        )
        self.assertQuerySetEqual(
            publishers,
            ["Sams", "Morgan Kaufmann", "Expensive Publisher"],
            lambda p: p.name,
        )

        publishers = Publisher.objects.annotate(num_books=Count("book")).filter(
            num_books__isnull=True
        )
        self.assertEqual(len(publishers), 0)