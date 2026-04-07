def test_filter_by_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.filter(
            field__len=models.OuterRef("field__len"),
        ).values("field")
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.alias(
                same_sized_fields=ArraySubquery(inner_qs),
            ).filter(same_sized_fields__len__gt=1),
            self.objs[0:2],
        )