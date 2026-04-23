def test_annotate_defer_select_related(self):
        qs = (
            Book.objects.select_related("contact")
            .annotate(page_sum=Sum("pages"))
            .defer("name")
            .filter(pk=self.b1.pk)
        )

        rows = [
            (
                self.b1.id,
                "159059725",
                447,
                "Adrian Holovaty",
                "The Definitive Guide to Django: Web Development Done Right",
            )
        ]
        self.assertQuerySetEqual(
            qs.order_by("pk"),
            rows,
            lambda r: (r.id, r.isbn, r.page_sum, r.contact.name, r.name),
        )