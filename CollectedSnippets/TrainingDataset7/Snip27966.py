def test_rel_db_type(self):
        field = self.model._meta.get_field("value")
        rel_db_type = field.rel_db_type(connection)
        self.assertEqual(rel_db_type, self.rel_db_type_class().db_type(connection))