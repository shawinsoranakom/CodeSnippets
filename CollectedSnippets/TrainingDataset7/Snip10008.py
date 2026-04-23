def last_executed_query(self, cursor, sql, params):
        # Python substitutes parameters in Modules/_sqlite/cursor.c with:
        # bind_parameters(state, self->statement, parameters);
        # Unfortunately there is no way to reach self->statement from Python,
        # so we quote and substitute parameters manually.
        if params:
            if isinstance(params, (list, tuple)):
                params = self._quote_params_for_last_executed_query(params)
            else:
                values = tuple(params.values())
                values = self._quote_params_for_last_executed_query(values)
                params = dict(zip(params, values))
            return sql % params
        # For consistency with SQLiteCursorWrapper.execute(), just return sql
        # when there are no parameters. See #13648 and #17158.
        else:
            return sql