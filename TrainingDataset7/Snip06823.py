def __init__(self, expression, *args, **extra):
        nargs = len(args)
        expressions = [expression]
        if nargs in (1, 2):
            expressions.extend(
                [self._handle_param(arg, "", NUMERIC_TYPES) for arg in args]
            )
        elif nargs == 4:
            # Reverse origin and size param ordering
            expressions += [
                *(self._handle_param(arg, "", NUMERIC_TYPES) for arg in args[2:]),
                *(self._handle_param(arg, "", NUMERIC_TYPES) for arg in args[0:2]),
            ]
        else:
            raise ValueError("Must provide 1, 2, or 4 arguments to `SnapToGrid`.")
        super().__init__(*expressions, **extra)