def wrapper(*args: P.args, **kwargs: P.kwargs) -> pw.Table:
        cols = {}
        i = itertools.count()
        table: pw.Table | None = None
        for arg in itertools.chain(args, kwargs.values()):
            if isinstance(arg, pw.ColumnReference):
                table = arg.table
                cols[f"_pw_{next(i)}"] = arg

        assert (
            table is not None
        ), "at least one argument to function wrapped by _predict_asof_now should be a ColumnReference"

        queries_table = table.select(**cols)
        queries_table = queries_table._forget_immediately()

        i = itertools.count()
        new_args = []
        new_kwargs = {}
        for arg in args:
            if isinstance(arg, pw.ColumnReference):
                new_args.append(queries_table[f"_pw_{next(i)}"])
            else:
                new_args.append(arg)
        for name, kwarg in kwargs.items():
            if isinstance(kwarg, pw.ColumnReference):
                new_kwargs[name] = queries_table[f"_pw_{next(i)}"]
            else:
                new_kwargs[name] = kwarg

        result = prediction_function(*new_args, **new_kwargs)
        result = result.filter_out_results_of_forgetting(ensure_consistency=False)
        if with_queries_universe:
            # FIXME assert that table is append-only,
            # then results should also be append-only (promise that)
            # then we should have a version of with_universe_of for both append only tables
            # that frees memory when records are joined
            result = result.with_universe_of(table)
        return result