def assertTableExists(self, table, using="default"):
        with connections[using].cursor() as cursor:
            self.assertIn(table, connections[using].introspection.table_names(cursor))