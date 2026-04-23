def test_deconstruct_deferrable(self):
        constraint = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[("datespan", RangeOperators.OVERLAPS)],
            deferrable=Deferrable.DEFERRED,
        )
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(
            path, "django.contrib.postgres.constraints.ExclusionConstraint"
        )
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "name": "exclude_overlapping",
                "expressions": [("datespan", RangeOperators.OVERLAPS)],
                "deferrable": Deferrable.DEFERRED,
            },
        )