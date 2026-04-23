def _fix_for_params(self, query, params, unify_by_values=False):
        # oracledb wants no trailing ';' for SQL statements. For PL/SQL, it
        # does want a trailing ';' but not a trailing '/'. However, these
        # characters must be included in the original query in case the query
        # is being passed to SQL*Plus.
        if query.endswith(";") or query.endswith("/"):
            query = query[:-1]
        if params is None:
            params = []
        elif hasattr(params, "keys"):
            # Handle params as dict
            args = {k: ":%s" % k for k in params}
            query %= args
        elif unify_by_values and params:
            # Handle params as a dict with unified query parameters by their
            # values. It can be used only in single query execute() because
            # executemany() shares the formatted query with each of the params
            # list. e.g. for input params = [0.75, 2, 0.75, 'sth', 0.75]
            # params_dict = {
            #     (float, 0.75): ':arg0',
            #     (int, 2): ':arg1',
            #     (str, 'sth'): ':arg2',
            # }
            # args = [':arg0', ':arg1', ':arg0', ':arg2', ':arg0']
            # params = {':arg0': 0.75, ':arg1': 2, ':arg2': 'sth'}
            # The type of parameters in param_types keys is necessary to avoid
            # unifying 0/1 with False/True.
            param_types = [(type(param), param) for param in params]
            params_dict = {
                param_type: ":arg%d" % i
                for i, param_type in enumerate(dict.fromkeys(param_types))
            }
            args = [params_dict[param_type] for param_type in param_types]
            params = {
                placeholder: param for (_, param), placeholder in params_dict.items()
            }
            query %= tuple(args)
        else:
            # Handle params as sequence
            args = [(":arg%d" % i) for i in range(len(params))]
            query %= tuple(args)
        return query, self._format_params(params)