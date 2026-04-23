def test_filter_conditional_annotation(self):
        qs = (
            Employee.objects.annotate(
                rank=Window(Rank(), partition_by="department", order_by="-salary"),
                case_first_rank=Case(
                    When(rank=1, then=True),
                    default=False,
                ),
                q_first_rank=Q(rank=1),
            )
            .order_by("name")
            .values_list("name", flat=True)
        )
        for annotation in ["case_first_rank", "q_first_rank"]:
            with self.subTest(annotation=annotation):
                self.assertSequenceEqual(
                    qs.filter(**{annotation: True}),
                    ["Adams", "Johnson", "Miller", "Smith", "Wilkinson"],
                )