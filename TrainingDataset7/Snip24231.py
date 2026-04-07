def get_indexes(self, table):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
            return {
                name: constraint["columns"]
                for name, constraint in constraints.items()
                if constraint["index"]
            }