def test_query_encoding(self):
        """last_executed_query() returns a string."""
        data = RawData.objects.filter(raw_data=b"\x00\x46  \xfe").extra(
            select={"föö": 1}
        )
        sql, params = data.query.sql_with_params()
        with data.query.get_compiler("default").execute_sql(CURSOR) as cursor:
            last_sql = cursor.db.ops.last_executed_query(cursor, sql, params)
        self.assertIsInstance(last_sql, str)