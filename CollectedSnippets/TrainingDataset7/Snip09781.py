def pool(self):
        pool_options = self.settings_dict["OPTIONS"].get("pool")
        if self.alias == NO_DB_ALIAS or not pool_options:
            return None

        if self.alias not in self._connection_pools:
            if self.settings_dict.get("CONN_MAX_AGE", 0) != 0:
                raise ImproperlyConfigured(
                    "Pooling doesn't support persistent connections."
                )
            # Set the default options.
            if pool_options is True:
                pool_options = {}

            try:
                from psycopg_pool import ConnectionPool
            except ImportError as err:
                raise ImproperlyConfigured(
                    "Error loading psycopg_pool module.\nDid you install psycopg[pool]?"
                ) from err

            connect_kwargs = self.get_connection_params()
            # Ensure we run in autocommit, Django properly sets it later on.
            connect_kwargs["autocommit"] = True
            enable_checks = self.settings_dict["CONN_HEALTH_CHECKS"]
            pool = ConnectionPool(
                kwargs=connect_kwargs,
                open=False,  # Do not open the pool during startup.
                configure=self._configure_connection,
                check=ConnectionPool.check_connection if enable_checks else None,
                **pool_options,
            )
            # setdefault() ensures that multiple threads don't set this in
            # parallel. Since we do not open the pool during it's init above,
            # this means that at worst during startup multiple threads generate
            # pool objects and the first to set it wins.
            self._connection_pools.setdefault(self.alias, pool)

        return self._connection_pools[self.alias]