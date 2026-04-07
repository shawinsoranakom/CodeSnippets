def get_primary_key(self, table):
        with connection.cursor() as cursor:
            return connection.introspection.get_primary_key_column(cursor, table)