def executemany(self, sql, param_list):
        return self._execute_with_wrappers(
            sql, param_list, many=True, executor=self._executemany
        )