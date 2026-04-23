def test_annotated_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.exclude(
            pk=models.OuterRef("pk")
        ).values("order")
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.annotate(
                sibling_ids=ArraySubquery(inner_qs),
            )
            .get(order=1)
            .sibling_ids,
            [2, 3, 4, 5],
        )