def get_primary_key_columns(table):
        with connection.cursor() as cursor:
            return connection.introspection.get_primary_key_columns(cursor, table)