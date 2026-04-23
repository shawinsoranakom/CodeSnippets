def __init__(self, table, params):
        super().__init__(params)
        self._table = table

        class CacheEntry:
            _meta = Options(table)

        self.cache_model_class = CacheEntry