def _collapse_arguments(cls, args, **assumptions):
        """Remove redundant args.

        Examples
        ========

        >>> from sympy import Min, Max
        >>> from sympy.abc import a, b, c, d, e

        Any arg in parent that appears in any
        parent-like function in any of the flat args
        of parent can be removed from that sub-arg:

        >>> Min(a, Max(b, Min(a, c, d)))
        Min(a, Max(b, Min(c, d)))

        If the arg of parent appears in an opposite-than parent
        function in any of the flat args of parent that function
        can be replaced with the arg:

        >>> Min(a, Max(b, Min(c, d, Max(a, e))))
        Min(a, Max(b, Min(a, c, d)))
        """
        if not args:
            return args
        args = list(ordered(args))
        if cls is Min:
            other = Max
        else:
            other = Min  # type: ignore[assignment]

        # find global comparable max of Max and min of Min if a new
        # value is being introduced in these args at position 0 of
        # the ordered args
        if args[0].is_number:
            sifted = mins, maxs = [], []  # type: ignore[var-annotated]
            for i in args:
                for v in walk(i, Min, Max):
                    if v.args[0].is_comparable:
                        sifted[isinstance(v, Max)].append(v)
            small = Min.identity
            for i in mins:
                v = i.args[0]
                if v.is_number and (v < small) == True:  # noqa: E712
                    small = v
            big = Max.identity
            for i in maxs:
                v = i.args[0]
                if v.is_number and (v > big) == True:  # noqa: E712
                    big = v
            # at the point when this function is called from __new__,
            # there may be more than one numeric arg present since
            # local zeros have not been handled yet, so look through
            # more than the first arg
            if cls is Min:
                for arg in args:
                    if not arg.is_number:
                        break
                    if (arg < small) == True:  # noqa: E712
                        small = arg
            elif cls == Max:
                for arg in args:
                    if not arg.is_number:
                        break
                    if (arg > big) == True:  # noqa: E712
                        big = arg
            T = None
            if cls is Min:
                if small != Min.identity:
                    other = Max
                    T = small
            elif big != Max.identity:
                other = Min  # type: ignore[assignment]
                T = big
            if T is not None:
                # remove numerical redundancy
                for i in range(len(args)):
                    a = args[i]
                    if isinstance(a, other):
                        a0 = a.args[0]
                        if (  # noqa: E712
                            (a0 > T) if other == Max else (a0 < T)
                        ) == True:
                            args[i] = cls.identity  # type: ignore[attr-defined]

        # remove redundant symbolic args
        def do(ai, a):
            if not isinstance(ai, (Min, Max)):
                return ai
            cond = a in ai.args
            if not cond:
                return ai.func(*[do(i, a) for i in ai.args], evaluate=False)
            if isinstance(ai, cls):
                return ai.func(*[do(i, a) for i in ai.args if i != a], evaluate=False)
            return a

        for i, a in enumerate(args):
            args[i + 1 :] = [do(ai, a) for ai in args[i + 1 :]]

        # factor out common elements as for
        # Min(Max(x, y), Max(x, z)) -> Max(x, Min(y, z))
        # and vice versa when swapping Min/Max -- do this only for the
        # easy case where all functions contain something in common;
        # trying to find some optimal subset of args to modify takes
        # too long

        def factor_minmax(args):
            is_other = lambda arg: isinstance(arg, other)  # noqa: E731
            other_args, remaining_args = sift(args, is_other, binary=True)
            if not other_args:
                return args

            # Min(Max(x, y, z), Max(x, y, u, v)) -> {x,y}, ({z}, {u,v})
            arg_sets = [set(arg.args) for arg in other_args]
            common = set.intersection(*arg_sets)
            if not common:
                return args

            new_other_args = list(common)
            arg_sets_diff = [arg_set - common for arg_set in arg_sets]

            # If any set is empty after removing common then all can be
            # discarded e.g. Min(Max(a, b, c), Max(a, b)) -> Max(a, b)
            if all(arg_sets_diff):
                other_args_diff = [other(*s, evaluate=False) for s in arg_sets_diff]
                new_other_args.append(cls(*other_args_diff, evaluate=False))

            other_args_factored = other(*new_other_args, evaluate=False)
            return remaining_args + [other_args_factored]

        if len(args) > 1:
            args = factor_minmax(args)

        return args