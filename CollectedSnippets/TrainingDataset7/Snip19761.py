def get_constraints(table):
    with connection.cursor() as cursor:
        return connection.introspection.get_constraints(cursor, table)