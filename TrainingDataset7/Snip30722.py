def test_distinct_ordered_sliced_subquery(self):
        # Implicit values('id').
        self.assertSequenceEqual(
            NamedCategory.objects.filter(
                id__in=NamedCategory.objects.distinct().order_by("name")[0:2],
            )
            .order_by("name")
            .values_list("name", flat=True),
            ["first", "fourth"],
        )
        # Explicit values('id').
        self.assertSequenceEqual(
            NamedCategory.objects.filter(
                id__in=NamedCategory.objects.distinct()
                .order_by("-name")
                .values("id")[0:2],
            )
            .order_by("name")
            .values_list("name", flat=True),
            ["second", "third"],
        )
        # Annotated value.
        self.assertSequenceEqual(
            DumbCategory.objects.filter(
                id__in=DumbCategory.objects.annotate(double_id=F("id") * 2)
                .order_by("id")
                .distinct()
                .values("double_id")[0:2],
            )
            .order_by("id")
            .values_list("id", flat=True),
            [2, 4],
        )