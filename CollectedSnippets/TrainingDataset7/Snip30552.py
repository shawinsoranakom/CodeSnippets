def test_rawsql_annotation(self):
        query = Query(None)
        sql = "%s = 1"
        # Wrap with a CASE WHEN expression if a database backend (e.g. Oracle)
        # doesn't support boolean expression in SELECT list.
        if not connection.features.supports_boolean_expr_in_select_clause:
            sql = f"CASE WHEN {sql} THEN 1 ELSE 0 END"
        query.add_annotation(RawSQL(sql, (1,), BooleanField()), "_check")
        result = query.get_compiler(using=DEFAULT_DB_ALIAS).execute_sql(SINGLE)
        self.assertEqual(result[0], 1)