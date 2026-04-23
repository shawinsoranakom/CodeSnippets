def test_valid_default(self):
        class MyModel(PostgreSQLModel):
            field = HStoreField(default=dict)

        self.assertEqual(MyModel().check(), [])