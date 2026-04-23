def _base_delete_many(self, keys):
        if not keys:
            return False

        db = router.db_for_write(self.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name
        table = quote_name(self._table)

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM %s WHERE %s IN (%s)"
                % (
                    table,
                    quote_name("cache_key"),
                    ", ".join(["%s"] * len(keys)),
                ),
                keys,
            )
            return bool(cursor.rowcount)