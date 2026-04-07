def test_deconstruct_include(self):
        constraint = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[("datespan", RangeOperators.OVERLAPS)],
            include=["cancelled", "room"],
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
                "include": ("cancelled", "room"),
            },
        )