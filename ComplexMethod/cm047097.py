def execute(self, query, params=None, log_exceptions: bool = True) -> None:
        global sql_counter

        if isinstance(query, SQL):
            assert params is None, "Unexpected parameters for SQL query object"
            query, params = query.code, query.params

        if params and not isinstance(params, (tuple, list, dict)):
            # psycopg2's TypeError is not clear if you mess up the params
            raise ValueError("SQL query parameters should be a tuple, list or dict; got %r" % (params,))

        start = real_time()
        try:
            self._obj.execute(query, params)
        except Exception as e:
            if log_exceptions:
                _logger.error("bad query: %s\nERROR: %s", self._obj.query or query, e)
            raise
        finally:
            delay = real_time() - start
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug("[%.3f ms] query: %s", 1000 * delay, self._format(query, params))

        # simple query count is always computed
        self.sql_log_count += 1
        sql_counter += 1

        current_thread = threading.current_thread()
        if hasattr(current_thread, 'query_count'):
            current_thread.query_count += 1
        if hasattr(current_thread, 'query_time'):
            current_thread.query_time += delay

        # optional hooks for performance and tracing analysis
        for hook in getattr(current_thread, 'query_hooks', ()):
            hook(self, query, params, start, delay)

        # advanced stats
        if _logger.isEnabledFor(logging.DEBUG):
            if obj_query := self._obj.query:
                query = obj_query.decode()
            query_type, table = categorize_query(query)
            log_target = None
            if query_type == 'into':
                log_target = self.sql_into_log
            elif query_type == 'from':
                log_target = self.sql_from_log
            if log_target:
                stat_count, stat_time = log_target.get(table or '', (0, 0))
                log_target[table or ''] = (stat_count + 1, stat_time + delay * 1E6)
        return None