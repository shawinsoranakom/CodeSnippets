def test_union_multiple_models_with_values_list_and_order(self):
        reserved_name = ReservedName.objects.create(name="rn1", order=0)
        qs1 = Celebrity.objects.all()
        qs2 = ReservedName.objects.all()
        self.assertSequenceEqual(
            qs1.union(qs2).order_by("name").values_list("pk", flat=True),
            [reserved_name.pk],
        )