def get_table_description(self, table, using="default"):
        with connections[using].cursor() as cursor:
            return connections[using].introspection.get_table_description(cursor, table)