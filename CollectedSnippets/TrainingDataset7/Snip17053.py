def test_unused_aliased_aggregate_and_annotation_reverse_fk(self):
        Book.objects.create(
            name="b3",
            publisher=self.p2,
            pages=1000,
            rating=4.2,
            price=50,
            contact=self.a2,
            pubdate=datetime.date.today(),
        )
        qs = Publisher.objects.annotate(
            total_pages=Sum("book__pages"),
            good_book=Case(
                When(book__rating__gt=4.0, then=Value(True)),
                default=Value(False),
            ),
        )
        self.assertEqual(qs.count(), 3)