def _ensure_vector_column_exists(self, table_name: str, vector_size: int, refresh_metadata: bool = True):
        """
        Ensure vector column and index exist for the given vector size.
        This method is safe to call multiple times - it will skip if already exists.
        Uses cache to avoid repeated INFORMATION_SCHEMA queries.

        Args:
            table_name: Name of the table
            vector_size: Size of the vector column
            refresh_metadata: Whether to refresh SQLAlchemy metadata after changes (default True)
        """
        if vector_size <= 0:
            return

        cache_key = (table_name, vector_size)

        # Check cache first
        if cache_key in self._vector_column_cache:
            return

        lock_prefix = self.get_lock_prefix()
        vector_field_name = f"q_{vector_size}_vec"
        vector_index_name = f"{vector_field_name}_idx"

        # Check if already exists (may have been created by another process)
        column_exists = self._column_exist(table_name, vector_field_name)
        index_exists = self._index_exists(table_name, vector_index_name)

        if column_exists and index_exists:
            # Already exists, add to cache and return
            with self._vector_column_cache_lock:
                self._vector_column_cache.add(cache_key)
            return

        # Create column if needed
        if not column_exists:
            _try_with_lock(
                lock_name=f"{lock_prefix}add_vector_column_{table_name}_{vector_field_name}",
                check_func=lambda: self._column_exist(table_name, vector_field_name),
                process_func=lambda: self._add_vector_column(table_name, vector_size),
            )

        # Create index if needed
        if not index_exists:
            _try_with_lock(
                lock_name=f"{lock_prefix}add_vector_idx_{table_name}_{vector_field_name}",
                check_func=lambda: self._index_exists(table_name, vector_index_name),
                process_func=lambda: self._add_vector_index(table_name, vector_field_name),
            )

        if refresh_metadata:
            self.client.refresh_metadata([table_name])

        # Add to cache after successful creation
        with self._vector_column_cache_lock:
            self._vector_column_cache.add(cache_key)