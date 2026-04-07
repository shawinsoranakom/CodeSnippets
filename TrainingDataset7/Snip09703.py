def cache_key_culling_sql(self):
        cache_key = self.quote_name("cache_key")
        return (
            f"SELECT {cache_key} "
            f"FROM %s "
            f"ORDER BY {cache_key} OFFSET %%s ROWS FETCH FIRST 1 ROWS ONLY"
        )