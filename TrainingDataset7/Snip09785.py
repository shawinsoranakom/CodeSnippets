def get_new_connection(self, conn_params):
        # self.isolation_level must be set:
        # - after connecting to the database in order to obtain the database's
        #   default when no value is explicitly specified in options.
        # - before calling _set_autocommit() because if autocommit is on, that
        #   will set connection.isolation_level to ISOLATION_LEVEL_AUTOCOMMIT.
        options = self.settings_dict["OPTIONS"]
        set_isolation_level = False
        try:
            isolation_level_value = options["isolation_level"]
        except KeyError:
            self.isolation_level = IsolationLevel.READ_COMMITTED
        else:
            # Set the isolation level to the value from OPTIONS.
            try:
                self.isolation_level = IsolationLevel(isolation_level_value)
                set_isolation_level = True
            except ValueError:
                raise ImproperlyConfigured(
                    f"Invalid transaction isolation level {isolation_level_value} "
                    f"specified. Use one of the psycopg.IsolationLevel values."
                )
        if self.pool:
            # If nothing else has opened the pool, open it now.
            self.pool.open()
            connection = self.pool.getconn()
        else:
            connection = self.Database.connect(**conn_params)
        if set_isolation_level:
            connection.isolation_level = self.isolation_level
        if not is_psycopg3:
            # Register dummy loads() to avoid a round trip from psycopg2's
            # decode to json.dumps() to json.loads(), when using a custom
            # decoder in JSONField.
            psycopg2.extras.register_default_jsonb(
                conn_or_curs=connection, loads=lambda x: x
            )
        return connection