def mogrify(sql, params, connection):
        with connection.cursor() as cursor:
            return cursor.mogrify(sql, params).decode()