def test_count_preserve_group_by(self):
        # new release of the same book
        Book.objects.create(
            isbn="113235613",
            name=self.b4.name,
            pages=self.b4.pages,
            rating=4.0,
            price=Decimal("39.69"),
            contact=self.a5,
            publisher=self.p3,
            pubdate=datetime.date(2018, 11, 3),
        )
        qs = Book.objects.values("contact__name", "publisher__name").annotate(
            publications=Count("id")
        )
        self.assertEqual(qs.order_by("id").count(), len(qs.order_by("id")))
        self.assertEqual(qs.extra(order_by=["id"]).count(), len(qs.order_by("id")))