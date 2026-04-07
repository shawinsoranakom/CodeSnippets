def _base_set(self, mode, key, value, timeout=DEFAULT_TIMEOUT):
        timeout = self.get_backend_timeout(timeout)
        db = router.db_for_write(self.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name
        table = quote_name(self._table)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM %s" % table)
            num = cursor.fetchone()[0]
            now = tz_now()
            now = now.replace(microsecond=0)
            if timeout is None:
                exp = datetime.max
            else:
                tz = UTC if settings.USE_TZ else None
                exp = datetime.fromtimestamp(timeout, tz=tz)
            exp = exp.replace(microsecond=0)
            if num > self._max_entries:
                self._cull(db, cursor, now, num)
            pickled = pickle.dumps(value, self.pickle_protocol)
            # The DB column is expecting a string, so make sure the value is a
            # string, not bytes. Refs #19274.
            b64encoded = base64.b64encode(pickled).decode("latin1")
            try:
                # Note: typecasting for datetimes is needed by some 3rd party
                # database backends. All core backends work without
                # typecasting, so be careful about changes here - test suite
                # will NOT pick regressions.
                with transaction.atomic(using=db):
                    cursor.execute(
                        "SELECT %s, %s FROM %s WHERE %s = %%s"
                        % (
                            quote_name("cache_key"),
                            quote_name("expires"),
                            table,
                            quote_name("cache_key"),
                        ),
                        [key],
                    )
                    result = cursor.fetchone()

                    if result:
                        current_expires = result[1]
                        expression = models.Expression(
                            output_field=models.DateTimeField()
                        )
                        for converter in connection.ops.get_db_converters(
                            expression
                        ) + expression.get_db_converters(connection):
                            current_expires = converter(
                                current_expires, expression, connection
                            )

                    exp = connection.ops.adapt_datetimefield_value(exp)
                    if result and mode == "touch":
                        cursor.execute(
                            "UPDATE %s SET %s = %%s WHERE %s = %%s"
                            % (table, quote_name("expires"), quote_name("cache_key")),
                            [exp, key],
                        )
                    elif result and (
                        mode == "set" or (mode == "add" and current_expires < now)
                    ):
                        cursor.execute(
                            "UPDATE %s SET %s = %%s, %s = %%s WHERE %s = %%s"
                            % (
                                table,
                                quote_name("value"),
                                quote_name("expires"),
                                quote_name("cache_key"),
                            ),
                            [b64encoded, exp, key],
                        )
                    elif mode != "touch":
                        cursor.execute(
                            "INSERT INTO %s (%s, %s, %s) VALUES (%%s, %%s, %%s)"
                            % (
                                table,
                                quote_name("cache_key"),
                                quote_name("value"),
                                quote_name("expires"),
                            ),
                            [key, b64encoded, exp],
                        )
                    else:
                        return False  # touch failed.
            except DatabaseError:
                # To be threadsafe, updates/inserts are allowed to fail
                # silently
                return False
            else:
                return True