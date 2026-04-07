def test_nested_field_checks(self):
        """
        Nested ArrayFields are permitted.
        """

        class MyModel(PostgreSQLModel):
            field = ArrayField(ArrayField(models.CharField(max_length=-1)))

        model = MyModel()
        errors = model.check()
        self.assertEqual(len(errors), 1)
        # The inner CharField has a non-positive max_length.
        self.assertEqual(errors[0].id, "postgres.E001")
        self.assertIn("max_length", errors[0].msg)