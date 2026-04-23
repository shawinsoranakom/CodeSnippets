def assertTableNotExists(self, table):
        with connection.cursor() as cursor:
            self.assertNotIn(table, connection.introspection.table_names(cursor))