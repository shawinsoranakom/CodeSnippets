def debug_sql(
        self, sql=None, params=None, use_last_executed_query=False, many=False
    ):
        start = time.monotonic()
        try:
            yield
        finally:
            stop = time.monotonic()
            duration = stop - start
            if use_last_executed_query:
                sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            try:
                times = len(params) if many else ""
            except TypeError:
                # params could be an iterator.
                times = "?"
            self.db.queries_log.append(
                {
                    "sql": "%s times: %s" % (times, sql) if many else sql,
                    "time": "%.3f" % duration,
                }
            )
            logger.debug(
                "(%.3f) %s; args=%s; alias=%s",
                duration,
                sql,
                params,
                self.db.alias,
                extra={
                    "duration": duration,
                    "sql": sql,
                    "params": params,
                    "alias": self.db.alias,
                },
            )