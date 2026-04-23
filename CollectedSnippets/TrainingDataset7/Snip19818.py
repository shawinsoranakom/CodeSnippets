def test_deconstruction_with_opclasses(self):
        fields = ["foo", "bar"]
        name = "unique_fields"
        opclasses = ["varchar_pattern_ops", "text_pattern_ops"]
        constraint = models.UniqueConstraint(
            fields=fields, name=name, opclasses=opclasses
        )
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.UniqueConstraint")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": tuple(fields),
                "name": name,
                "opclasses": opclasses,
            },
        )