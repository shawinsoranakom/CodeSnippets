def _cull(self, db, cursor, now, num):
        if self._cull_frequency == 0:
            self.clear()
        else:
            connection = connections[db]
            table = connection.ops.quote_name(self._table)
            cursor.execute(
                "DELETE FROM %s WHERE %s < %%s"
                % (
                    table,
                    connection.ops.quote_name("expires"),
                ),
                [connection.ops.adapt_datetimefield_value(now)],
            )
            deleted_count = cursor.rowcount
            remaining_num = num - deleted_count
            if remaining_num > self._max_entries:
                cull_num = remaining_num // self._cull_frequency
                cursor.execute(
                    connection.ops.cache_key_culling_sql() % table, [cull_num]
                )
                last_cache_key = cursor.fetchone()
                if last_cache_key:
                    cursor.execute(
                        "DELETE FROM %s WHERE %s < %%s"
                        % (
                            table,
                            connection.ops.quote_name("cache_key"),
                        ),
                        [last_cache_key[0]],
                    )