def test_base_field_check_kwargs(self):
        passed_kwargs = None

        class MyField(models.Field):
            def check(self, **kwargs):
                nonlocal passed_kwargs
                passed_kwargs = kwargs
                return []

        class MyModel(PostgreSQLModel):
            field = ArrayField(MyField())

        self.assertEqual(MyModel.check(databases=["default"]), [])
        self.assertEqual(
            passed_kwargs,
            {"databases": ["default"]},
            "ArrayField.check kwargs should be passed to its base_field.",
        )