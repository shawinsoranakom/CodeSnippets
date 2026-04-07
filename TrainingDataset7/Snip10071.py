def executemany(self, sql, param_list):
        with self.debug_sql(sql, param_list, many=True):
            return super().executemany(sql, param_list)