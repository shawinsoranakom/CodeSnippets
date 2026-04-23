def execute(self, query, params=None):
        query, params = self._fix_for_params(query, params, unify_by_values=True)
        self._guess_input_sizes([params])
        with wrap_oracle_errors():
            return self.cursor.execute(query, self._param_generator(params))