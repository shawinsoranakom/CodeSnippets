def _check_url_hot_query(self, url, expected_query_count, select_tables_perf=None, insert_tables_perf=None, nocache=False):
        query_count, sql_queries = self._get_url_hot_query(url, query_list=True, nocache=nocache)

        sql_from_tables = {}
        sql_into_tables = {}

        query_separator = '\n' + '-' * 100 + '\n'
        queries = query_separator.join(sql_queries)

        for query in sql_queries:
            query_type, table = categorize_query(query)
            if query_type == 'into':
                log_target = sql_into_tables
            elif query_type == 'from':
                log_target = sql_from_tables
            else:
                _logger.warning("Query type %s for query %s is not supported by _check_url_hot_query", query_type, query)
            log_target.setdefault(table, 0)
            log_target[table] = log_target[table] + 1

        if not select_tables_perf:
            select_tables_perf = {}
        select = {}
        for key in (set(sql_from_tables) | set(select_tables_perf)):
            value = sql_from_tables.get(key, 0) - select_tables_perf.get(key, 0)
            if value:
                select[key] = value

        if not insert_tables_perf:
            insert_tables_perf = {}
        insert = {}
        for key in (set(sql_into_tables) | set(insert_tables_perf)):
            value = sql_into_tables.get(key, 0) - insert_tables_perf.get(key, 0)
            if value:
                insert[key] = value

        if query_count != expected_query_count:
            msq = f"Expected {expected_query_count} queries but {query_count} where ran:\nDiff of select queries: {select}\nDiff of insert queries: {insert}{query_separator}{queries}{query_separator}"
            self.fail(msq)

        self.assertDictEqual(sql_from_tables, select_tables_perf, f'Select queries does not match: {select}{query_separator}{queries}{query_separator}')
        self.assertDictEqual(sql_into_tables, insert_tables_perf, f'Insert queries does not match: {insert}{query_separator}{queries}{query_separator}')