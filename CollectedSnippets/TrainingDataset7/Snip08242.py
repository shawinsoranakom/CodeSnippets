def get_many(self, keys, version=None):
        if not keys:
            return {}

        key_map = {
            self.make_and_validate_key(key, version=version): key for key in keys
        }

        db = router.db_for_read(self.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name
        table = quote_name(self._table)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT %s, %s, %s FROM %s WHERE %s IN (%s)"
                % (
                    quote_name("cache_key"),
                    quote_name("value"),
                    quote_name("expires"),
                    table,
                    quote_name("cache_key"),
                    ", ".join(["%s"] * len(key_map)),
                ),
                list(key_map),
            )
            rows = cursor.fetchall()

        result = {}
        expired_keys = []
        expression = models.Expression(output_field=models.DateTimeField())
        converters = connection.ops.get_db_converters(
            expression
        ) + expression.get_db_converters(connection)
        for key, value, expires in rows:
            for converter in converters:
                expires = converter(expires, expression, connection)
            if expires < tz_now():
                expired_keys.append(key)
            else:
                value = connection.ops.process_clob(value)
                value = pickle.loads(base64.b64decode(value.encode()))
                result[key_map.get(key)] = value
        self._base_delete_many(expired_keys)
        return result