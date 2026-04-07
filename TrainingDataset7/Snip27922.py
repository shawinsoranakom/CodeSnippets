def test_output_field_db_collation(self):
        collation = connection.features.test_collations["virtual"]
        m = self.output_field_db_collation_model.objects.create(name="NAME")
        field = m._meta.get_field("lower_name")
        db_parameters = field.db_parameters(connection)
        self.assertEqual(db_parameters["collation"], collation)
        self.assertEqual(db_parameters["type"], field.output_field.db_type(connection))