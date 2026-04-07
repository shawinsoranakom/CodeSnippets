def test_deconstruction(self):
        fields = ["foo", "bar"]
        name = "unique_fields"
        constraint = models.UniqueConstraint(fields=fields, name=name)
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.UniqueConstraint")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"fields": tuple(fields), "name": name})