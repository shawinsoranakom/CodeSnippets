def cursor_execute(*queries):
    """
    Execute SQL queries using a new cursor on the default database connection.
    """
    results = []
    with connection.cursor() as cursor:
        for q in queries:
            results.append(cursor.execute(q))
    return results