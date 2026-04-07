def test_last_executed_query(self):
        # last_executed_query() interpolate all parameters, in most cases it is
        # not equal to QuerySet.query.
        for qs in (
            Article.objects.filter(pk=1),
            Article.objects.filter(pk__in=(1, 2), reporter__pk=3),
            Article.objects.filter(
                pk=1,
                reporter__pk=9,
            ).exclude(reporter__pk__in=[2, 1]),
            Article.objects.filter(pk__in=list(range(20, 31))),
        ):
            sql, params = qs.query.sql_with_params()
            with qs.query.get_compiler(DEFAULT_DB_ALIAS).execute_sql(CURSOR) as cursor:
                self.assertEqual(
                    cursor.db.ops.last_executed_query(cursor, sql, params),
                    str(qs.query),
                )