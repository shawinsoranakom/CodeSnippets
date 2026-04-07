def get_table_description(self, table):
        with connection.cursor() as cursor:
            return connection.introspection.get_table_description(cursor, table)