def test_adding_field_with_default(self):
        # See #22962
        table_name = "postgres_tests_integerarraydefaultmodel"
        with connection.cursor() as cursor:
            self.assertNotIn(table_name, connection.introspection.table_names(cursor))
        call_command("migrate", "postgres_tests", verbosity=0)
        with connection.cursor() as cursor:
            self.assertIn(table_name, connection.introspection.table_names(cursor))
        call_command("migrate", "postgres_tests", "zero", verbosity=0)
        with connection.cursor() as cursor:
            self.assertNotIn(table_name, connection.introspection.table_names(cursor))