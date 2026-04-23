def assertIndexExists(
        self, table, columns, value=True, using="default", index_type=None
    ):
        with connections[using].cursor() as cursor:
            self.assertEqual(
                value,
                any(
                    c["index"]
                    for c in connections[using]
                    .introspection.get_constraints(cursor, table)
                    .values()
                    if (
                        c["columns"] == list(columns)
                        and c["index"] is True
                        and (index_type is None or c["type"] == index_type)
                        and not c["unique"]
                    )
                ),
            )