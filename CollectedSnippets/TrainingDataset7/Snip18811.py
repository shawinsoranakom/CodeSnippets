def test_last_executed_query_dict(self):
        square_opts = Square._meta
        sql = "INSERT INTO %s (%s, %s) VALUES (%%(root)s, %%(square)s)" % (
            connection.introspection.identifier_converter(square_opts.db_table),
            connection.ops.quote_name(square_opts.get_field("root").column),
            connection.ops.quote_name(square_opts.get_field("square").column),
        )
        with connection.cursor() as cursor:
            params = {"root": 2, "square": 4}
            cursor.execute(sql, params)
            self.assertEqual(
                cursor.db.ops.last_executed_query(cursor, sql, params),
                sql % params,
            )