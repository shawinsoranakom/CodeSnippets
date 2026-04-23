def test_deconstruction_with_include(self):
        fields = ["foo", "bar"]
        name = "unique_fields"
        include = ["baz_1", "baz_2"]
        constraint = models.UniqueConstraint(fields=fields, name=name, include=include)
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.UniqueConstraint")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": tuple(fields),
                "name": name,
                "include": tuple(include),
            },
        )