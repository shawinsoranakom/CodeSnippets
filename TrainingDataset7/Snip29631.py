def test_valid_default_none(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.IntegerField(), default=None)

        model = MyModel()
        self.assertEqual(model.check(), [])