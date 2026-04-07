def close_pool(self):
        if self.pool:
            self.pool.close()
            del self._connection_pools[self.alias]