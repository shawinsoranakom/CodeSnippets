def test_durationfield_multiply_divide(self):
        Experiment.objects.update(scalar=2)
        tests = [
            (Decimal("2"), 2),
            (F("scalar"), 2),
            (2, 2),
            (3.2, 3.2),
        ]
        for expr, scalar in tests:
            with self.subTest(expr=expr):
                qs = Experiment.objects.annotate(
                    multiplied=ExpressionWrapper(
                        expr * F("estimated_time"),
                        output_field=DurationField(),
                    ),
                    divided=ExpressionWrapper(
                        F("estimated_time") / expr,
                        output_field=DurationField(),
                    ),
                )
                for experiment in qs:
                    self.assertEqual(
                        experiment.multiplied,
                        experiment.estimated_time * scalar,
                    )
                    self.assertEqual(
                        experiment.divided,
                        experiment.estimated_time / scalar,
                    )