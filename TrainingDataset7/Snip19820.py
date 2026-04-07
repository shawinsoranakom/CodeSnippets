def test_deconstruction_with_expressions(self):
        name = "unique_fields"
        constraint = models.UniqueConstraint(Lower("title"), name=name)
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.UniqueConstraint")
        self.assertEqual(args, (Lower("title"),))
        self.assertEqual(kwargs, {"name": name})