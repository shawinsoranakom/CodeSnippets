def assertTableExists(self, table):
        with connection.cursor() as cursor:
            self.assertIn(table, connection.introspection.table_names(cursor))