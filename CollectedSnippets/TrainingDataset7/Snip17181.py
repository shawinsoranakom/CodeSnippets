def test_grouping_by_q_expression_annotation(self):
        authors = (
            Author.objects.annotate(
                under_40=ExpressionWrapper(Q(age__lt=40), output_field=BooleanField()),
            )
            .values("under_40")
            .annotate(
                count_id=Count("id"),
            )
            .values("under_40", "count_id")
        )
        self.assertCountEqual(
            authors,
            [
                {"under_40": False, "count_id": 3},
                {"under_40": True, "count_id": 6},
            ],
        )