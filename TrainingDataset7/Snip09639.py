def executemany(self, query, params=None):
        if not params:
            # No params given, nothing to do
            return None
        # uniform treatment for sequences and iterables
        params_iter = iter(params)
        query, firstparams = self._fix_for_params(query, next(params_iter))
        # we build a list of formatted params; as we're going to traverse it
        # more than once, we can't make it lazy by using a generator
        formatted = [firstparams] + [self._format_params(p) for p in params_iter]
        self._guess_input_sizes(formatted)
        with wrap_oracle_errors():
            return self.cursor.executemany(
                query, [self._param_generator(p) for p in formatted]
            )