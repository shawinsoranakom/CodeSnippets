def test_group_by_with_annotated_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.exclude(
            pk=models.OuterRef("pk")
        ).values("order")
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.annotate(
                sibling_ids=ArraySubquery(inner_qs),
                sibling_count=models.Max("sibling_ids__len"),
            ).values_list("sibling_count", flat=True),
            [len(self.objs) - 1] * len(self.objs),
        )