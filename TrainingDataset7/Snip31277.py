def assertForeignKeyNotExists(self, model, column, expected_fk_table):
        if not connection.features.can_introspect_foreign_keys:
            return
        with self.assertRaises(AssertionError):
            self.assertForeignKeyExists(model, column, expected_fk_table)