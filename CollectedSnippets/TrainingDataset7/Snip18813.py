def test_last_executed_query_with_duplicate_params(self):
        square_opts = Square._meta
        table = connection.introspection.identifier_converter(square_opts.db_table)
        id_column = connection.ops.quote_name(square_opts.get_field("id").column)
        root_column = connection.ops.quote_name(square_opts.get_field("root").column)
        sql = f"UPDATE {table} SET {root_column} = %s + %s WHERE {id_column} = %s"
        with connection.cursor() as cursor:
            params = [42, 42, 1]
            cursor.execute(sql, params)
            last_executed_query = connection.ops.last_executed_query(
                cursor, sql, params
            )
            self.assertEqual(
                last_executed_query,
                f"UPDATE {table} SET {root_column} = 42 + 42 WHERE {id_column} = 1",
            )