def test_deconstruction_with_deferrable(self):
        fields = ["foo"]
        name = "unique_fields"
        constraint = models.UniqueConstraint(
            fields=fields,
            name=name,
            deferrable=models.Deferrable.DEFERRED,
        )
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.UniqueConstraint")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": tuple(fields),
                "name": name,
                "deferrable": models.Deferrable.DEFERRED,
            },
        )