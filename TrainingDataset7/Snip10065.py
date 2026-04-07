def execute(self, sql, params=None):
        return self._execute_with_wrappers(
            sql, params, many=False, executor=self._execute
        )