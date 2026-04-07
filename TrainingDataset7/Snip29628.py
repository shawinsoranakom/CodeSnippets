def test_invalid_base_fields(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(
                models.ManyToManyField("postgres_tests.IntegerArrayModel")
            )

        model = MyModel()
        errors = model.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "postgres.E002")