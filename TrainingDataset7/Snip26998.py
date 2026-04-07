def assertIndexNameExists(self, table, index, using="default"):
        with connections[using].cursor() as cursor:
            self.assertIn(
                index,
                connection.introspection.get_constraints(cursor, table),
            )