def has_key(self, key, version=None):
        key = self.make_and_validate_key(key, version=version)

        db = router.db_for_read(self.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name

        now = tz_now().replace(microsecond=0, tzinfo=None)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT %s FROM %s WHERE %s = %%s and %s > %%s"
                % (
                    quote_name("cache_key"),
                    quote_name(self._table),
                    quote_name("cache_key"),
                    quote_name("expires"),
                ),
                [key, connection.ops.adapt_datetimefield_value(now)],
            )
            return cursor.fetchone() is not None