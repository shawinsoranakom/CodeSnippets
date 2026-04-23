def test_values_extra_grouping(self):
        # Regression for #10132 - If the values() clause only mentioned extra
        # (select=) columns, those columns are used for grouping
        qs = (
            Book.objects.extra(select={"pub": "publisher_id"})
            .values("pub")
            .annotate(Count("id"))
            .order_by("pub")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"pub": self.p1.id, "id__count": 2},
                {"pub": self.p2.id, "id__count": 1},
                {"pub": self.p3.id, "id__count": 2},
                {"pub": self.p4.id, "id__count": 1},
            ],
        )

        qs = (
            Book.objects.extra(select={"pub": "publisher_id", "foo": "pages"})
            .values("pub")
            .annotate(Count("id"))
            .order_by("pub")
        )
        self.assertSequenceEqual(
            qs,
            [
                {"pub": self.p1.id, "id__count": 2},
                {"pub": self.p2.id, "id__count": 1},
                {"pub": self.p3.id, "id__count": 2},
                {"pub": self.p4.id, "id__count": 1},
            ],
        )