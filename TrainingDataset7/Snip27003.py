def assertFKExists(self, table, columns, to, value=True, using="default"):
        if not connections[using].features.can_introspect_foreign_keys:
            return
        with connections[using].cursor() as cursor:
            self.assertEqual(
                value,
                any(
                    c["foreign_key"] == to
                    for c in connections[using]
                    .introspection.get_constraints(cursor, table)
                    .values()
                    if c["columns"] == list(columns)
                ),
            )