def _check_table_exists_cached(self, table_name: str) -> bool:
        """
        Check table existence with cache to reduce INFORMATION_SCHEMA queries.
        Thread-safe implementation using RLock.
        """
        if table_name in self._table_exists_cache:
            return True

        try:
            if not self.client.check_table_exists(table_name):
                return False

            # Check regular indexes
            for column_name in self.get_index_columns():
                if not self._index_exists(table_name, index_name_template % (table_name, column_name)):
                    return False

            # Check fulltext indexes
            for column_name in self.get_fulltext_columns():
                if not self._index_exists(table_name, fulltext_index_name_template % column_name):
                    return False

            # Check extra columns
            for column in self.get_extra_columns():
                if not self._column_exist(table_name, column.name):
                    return False

        except Exception as e:
            raise Exception(f"OBConnection._check_table_exists_cached error: {str(e)}")

        with self._table_exists_cache_lock:
            if table_name not in self._table_exists_cache:
                self._table_exists_cache.add(table_name)
        return True