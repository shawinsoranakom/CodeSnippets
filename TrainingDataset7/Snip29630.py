def test_valid_default(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.IntegerField(), default=list)

        model = MyModel()
        self.assertEqual(model.check(), [])