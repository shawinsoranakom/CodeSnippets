def test_aggregation_subquery_annotation_related_field(self):
        publisher = Publisher.objects.create(name=self.a9.name, num_awards=2)
        book = Book.objects.create(
            isbn="159059999",
            name="Test book.",
            pages=819,
            rating=2.5,
            price=Decimal("14.44"),
            contact=self.a9,
            publisher=publisher,
            pubdate=datetime.date(2019, 12, 6),
        )
        book.authors.add(self.a5, self.a6, self.a7)
        books_qs = (
            Book.objects.annotate(
                contact_publisher=Subquery(
                    Publisher.objects.filter(
                        pk=OuterRef("publisher"),
                        name=OuterRef("contact__name"),
                    ).values("name")[:1],
                )
            )
            .filter(
                contact_publisher__isnull=False,
            )
            .annotate(count=Count("authors"))
        )
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(books_qs, [book])
        if connection.features.allows_group_by_select_index:
            self.assertEqual(ctx[0]["sql"].count("SELECT"), 3)