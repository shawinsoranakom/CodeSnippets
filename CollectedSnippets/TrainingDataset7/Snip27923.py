def test_db_type_parameters(self):
        db_type_parameters = self.output_field_db_collation_model._meta.get_field(
            "lower_name"
        ).db_type_parameters(connection)
        self.assertEqual(db_type_parameters["max_length"], 11)