def execute_sql(
        self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE
    ):
        """
        Run the query against the database and return the result(s). The
        return value depends on the value of result_type.

        When result_type is:
        - MULTI: Retrieves all rows using fetchmany(). Wraps in an iterator for
           chunked reads when supported.
        - SINGLE: Retrieves a single row using fetchone().
        - ROW_COUNT: Retrieves the number of rows in the result.
        - CURSOR: Runs the query, and returns the cursor object. It is the
           caller's responsibility to close the cursor.
        """
        result_type = result_type or NO_RESULTS
        try:
            sql, params = self.as_sql()
            if not sql:
                raise EmptyResultSet
        except EmptyResultSet:
            if result_type == MULTI:
                return iter([])
            else:
                return
        if chunked_fetch:
            cursor = self.connection.chunked_cursor()
        else:
            cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
        except Exception as e:
            # Might fail for server-side cursors (e.g. connection closed)
            try:
                cursor.close()
            except DatabaseError:
                raise e from None
            raise

        if result_type == ROW_COUNT:
            try:
                return cursor.rowcount
            finally:
                cursor.close()
        if result_type == CURSOR:
            # Give the caller the cursor to process and close.
            return cursor
        if result_type == SINGLE:
            try:
                val = cursor.fetchone()
                if val:
                    return val[0 : self.col_count]
                return val
            finally:
                # done with the cursor
                cursor.close()
        if result_type == NO_RESULTS:
            cursor.close()
            return

        result = cursor_iter(
            cursor,
            self.connection.features.empty_fetchmany_value,
            self.col_count if self.has_extra_select else None,
            chunk_size,
        )
        if not chunked_fetch or not self.connection.features.can_use_chunked_reads:
            # If we are using non-chunked reads, we return the same data
            # structure as normally, but ensure it is all read into memory
            # before going any further. Use chunked_fetch if requested,
            # unless the database doesn't support it.
            return list(result)
        return result