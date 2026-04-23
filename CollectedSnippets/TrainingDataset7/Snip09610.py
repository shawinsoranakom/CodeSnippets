def pool(self):
        if not self.is_pool:
            return None

        if self.settings_dict.get("CONN_MAX_AGE", 0) != 0:
            raise ImproperlyConfigured(
                "Pooling doesn't support persistent connections."
            )

        pool_key = (self.alias, self.settings_dict["USER"])
        if pool_key not in self._connection_pools:
            connect_kwargs = self.get_connection_params()
            pool_options = connect_kwargs.pop("pool")
            if pool_options is not True:
                connect_kwargs.update(pool_options)

            pool = Database.create_pool(
                user=self.settings_dict["USER"],
                password=self.settings_dict["PASSWORD"],
                dsn=dsn(self.settings_dict),
                **connect_kwargs,
            )
            self._connection_pools.setdefault(pool_key, pool)

        return self._connection_pools[pool_key]