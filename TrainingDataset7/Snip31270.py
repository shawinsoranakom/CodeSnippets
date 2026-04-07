def get_constraints_count(self, table, column, fk_to):
        """
        Return a dict with keys 'fks', 'uniques, and 'indexes' indicating the
        number of foreign keys, unique constraints, and indexes on
        `table`.`column`. The `fk_to` argument is a 2-tuple specifying the
        expected foreign key relationship's (table, column).
        """
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        counts = {"fks": 0, "uniques": 0, "indexes": 0}
        for c in constraints.values():
            if c["columns"] == [column]:
                if c["foreign_key"] == fk_to:
                    counts["fks"] += 1
                if c["unique"]:
                    counts["uniques"] += 1
                elif c["index"]:
                    counts["indexes"] += 1
        return counts