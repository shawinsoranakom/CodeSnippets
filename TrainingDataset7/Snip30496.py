def test_union_with_values_list_on_annotated_and_unannotated(self):
        ReservedName.objects.create(name="rn1", order=1)
        qs1 = Number.objects.annotate(
            has_reserved_name=Exists(ReservedName.objects.filter(order=OuterRef("num")))
        ).filter(has_reserved_name=True)
        qs2 = Number.objects.filter(num=9)
        self.assertCountEqual(qs1.union(qs2).values_list("num", flat=True), [1, 9])