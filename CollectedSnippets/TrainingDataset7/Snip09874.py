def mogrify(sql, params, connection):
        with connection.cursor() as cursor:
            return ClientCursor(cursor.connection).mogrify(sql, params)