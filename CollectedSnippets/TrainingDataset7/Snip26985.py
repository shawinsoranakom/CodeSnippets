def assertTableNotExists(self, table, using="default"):
        with connections[using].cursor() as cursor:
            self.assertNotIn(
                table, connections[using].introspection.table_names(cursor)
            )