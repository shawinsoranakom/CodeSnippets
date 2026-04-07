def test_annotated_ordered_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.order_by("-order").values("order")
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.annotate(
                ids=ArraySubquery(inner_qs),
            )
            .first()
            .ids,
            [5, 4, 3, 2, 1],
        )