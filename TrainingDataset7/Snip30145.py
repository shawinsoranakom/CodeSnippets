def assertWhereContains(self, sql, needle):
        where_idx = sql.index("WHERE")
        self.assertEqual(
            sql.count(str(needle), where_idx),
            1,
            msg="WHERE clause doesn't contain %s, actual SQL: %s"
            % (needle, sql[where_idx:]),
        )