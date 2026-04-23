def test_annotate_defer(self):
        qs = (
            Book.objects.annotate(page_sum=Sum("pages"))
            .defer("name")
            .filter(pk=self.b1.pk)
        )

        rows = [
            (
                self.b1.id,
                "159059725",
                447,
                "The Definitive Guide to Django: Web Development Done Right",
            )
        ]
        self.assertQuerySetEqual(
            qs.order_by("pk"), rows, lambda r: (r.id, r.isbn, r.page_sum, r.name)
        )