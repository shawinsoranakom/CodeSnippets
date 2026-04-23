def test_deconstruct_output_field(self):
        value = Value("name", output_field=CharField())
        path, args, kwargs = value.deconstruct()
        self.assertEqual(path, "django.db.models.Value")
        self.assertEqual(args, (value.value,))
        self.assertEqual(len(kwargs), 1)
        self.assertEqual(
            kwargs["output_field"].deconstruct(), CharField().deconstruct()
        )