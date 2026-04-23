def close_pool(self):
        if self.pool:
            self.pool.close(force=True)
            pool_key = (self.alias, self.settings_dict["USER"])
            del self._connection_pools[pool_key]