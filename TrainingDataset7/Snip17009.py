def test_order_by_aggregate_transform(self):
        class Mod100(Mod, Transform):
            def __init__(self, expr):
                super().__init__(expr, 100)

        sum_field = IntegerField()
        sum_field.register_lookup(Mod100, "mod100")
        publisher_pages = (
            Book.objects.values("publisher")
            .annotate(sum_pages=Sum("pages", output_field=sum_field))
            .order_by("sum_pages__mod100")
        )
        self.assertQuerySetEqual(
            publisher_pages,
            [
                {"publisher": self.p2.id, "sum_pages": 528},
                {"publisher": self.p4.id, "sum_pages": 946},
                {"publisher": self.p1.id, "sum_pages": 747},
                {"publisher": self.p3.id, "sum_pages": 1482},
            ],
        )