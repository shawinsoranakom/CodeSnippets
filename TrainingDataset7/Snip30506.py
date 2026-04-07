def test_union_multiple_models_with_values_list_and_annotations(self):
        ReservedName.objects.create(name="rn1", order=10)
        Celebrity.objects.create(name="c1")
        qs1 = ReservedName.objects.annotate(row_type=Value("rn")).values_list(
            "name", "order", "row_type"
        )
        qs2 = Celebrity.objects.annotate(
            row_type=Value("cb"), order=Value(-10)
        ).values_list("name", "order", "row_type")
        self.assertSequenceEqual(
            qs1.union(qs2).order_by("order"),
            [("c1", -10, "cb"), ("rn1", 10, "rn")],
        )