def test_deconstruction_with_condition(self):
        fields = ["foo", "bar"]
        name = "unique_fields"
        condition = models.Q(foo=models.F("bar"))
        constraint = models.UniqueConstraint(
            fields=fields, name=name, condition=condition
        )
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.UniqueConstraint")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs, {"fields": tuple(fields), "name": name, "condition": condition}
        )