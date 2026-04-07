def assertIndexNameNotExists(self, table, index, using="default"):
        with connections[using].cursor() as cursor:
            self.assertNotIn(
                index,
                connection.introspection.get_constraints(cursor, table),
            )