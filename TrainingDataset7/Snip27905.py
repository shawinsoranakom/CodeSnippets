def test_deconstruct(self):
        field = GeneratedField(
            expression=F("a") + F("b"), output_field=IntegerField(), db_persist=True
        )
        _, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.GeneratedField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs["db_persist"], True)
        self.assertEqual(kwargs["expression"], F("a") + F("b"))
        self.assertEqual(
            kwargs["output_field"].deconstruct(), IntegerField().deconstruct()
        )