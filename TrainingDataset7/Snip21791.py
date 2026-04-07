def test_db_parameters_respects_db_type(self):
        f = CustomTypedField()
        self.assertEqual(f.db_parameters(connection)["type"], "custom_field")