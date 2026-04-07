def drop_collation():
            with connection.cursor() as cursor:
                cursor.execute(f"DROP COLLATION IF EXISTS {ci_collation}")