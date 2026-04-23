def test_union_multiple_models_with_values_list_and_order_by_extra_select(self):
        reserved_name = ReservedName.objects.create(name="rn1", order=0)
        qs1 = Celebrity.objects.extra(select={"extra_name": "name"})
        qs2 = ReservedName.objects.extra(select={"extra_name": "name"})
        self.assertSequenceEqual(
            qs1.union(qs2).order_by("extra_name").values_list("pk", flat=True),
            [reserved_name.pk],
        )