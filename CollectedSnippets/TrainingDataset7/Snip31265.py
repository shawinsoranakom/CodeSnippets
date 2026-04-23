def get_uniques(self, table):
        with connection.cursor() as cursor:
            return [
                c["columns"][0]
                for c in connection.introspection.get_constraints(
                    cursor, table
                ).values()
                if c["unique"] and len(c["columns"]) == 1
            ]