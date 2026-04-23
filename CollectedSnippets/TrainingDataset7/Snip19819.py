def test_deconstruction_with_nulls_distinct(self):
        fields = ["foo", "bar"]
        name = "unique_fields"
        constraint = models.UniqueConstraint(
            fields=fields, name=name, nulls_distinct=True
        )
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.UniqueConstraint")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": tuple(fields),
                "name": name,
                "nulls_distinct": True,
            },
        )