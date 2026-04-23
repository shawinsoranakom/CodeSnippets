def __new__(cls, *original_args, **assumptions):
        from sympy.core.parameters import global_parameters

        evaluate = assumptions.pop("evaluate", global_parameters.evaluate)
        args = (sympify(arg) for arg in original_args)

        # See the comment in _satisfy_unique_summations_symbols.
        unique_summations_symbols = (
            None
            if not evaluate
            else cls._satisfy_unique_summations_symbols(original_args)
        )

        if evaluate:
            try:
                # first standard filter, for cls.zero and cls.identity
                # also reshape Max(a, Max(b, c)) to Max(a, b, c)
                args = frozenset(cls._new_args_filter(args))  # type: ignore[assignment]
            except ShortCircuit:
                return cls.zero  # type: ignore[attr-defined]

            # No need to run _collapse_arguments and _find_localzeros, see the comment
            # in _satisfy_unique_summations_symbols.
            if unique_summations_symbols is None:
                # remove redundant args that are easily identified
                args = cls._collapse_arguments(args, **assumptions)

                # find local zeros
                args = cls._find_localzeros(args, **assumptions)

        args = frozenset(args)

        if not args:
            return cls.identity  # type: ignore[attr-defined]

        if len(args) == 1:
            return list(args).pop()

        # base creation
        obj = Expr.__new__(cls, *ordered(args), **assumptions)
        obj._argset = args

        obj.unique_summations_symbols = unique_summations_symbols
        return obj