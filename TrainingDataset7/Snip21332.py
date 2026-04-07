def test_filtering_on_annotate_that_uses_q(self):
        self.assertEqual(
            Company.objects.annotate(
                num_employees_check=ExpressionWrapper(
                    Q(num_employees__gt=3), output_field=BooleanField()
                )
            )
            .filter(num_employees_check=True)
            .count(),
            2,
        )