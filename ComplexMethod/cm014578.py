def _preparse(args: str) -> tuple[list[Argument], list[Argument], list[Argument]]:
        positional: list[Argument] = []
        kwarg_only: list[Argument] = []
        out: list[Argument] = []
        arguments_acc = positional

        # TODO: Use a real parser here; this will get bamboozled
        # by signatures that contain things like std::array<bool, 2> (note the space)
        for arg in args.split(", "):
            if not arg:
                continue
            if arg == "*":
                if arguments_acc is not positional:
                    raise AssertionError(
                        "invalid syntax: kwarg-only specifier * can only occur once"
                    )
                arguments_acc = kwarg_only
                continue
            parg = Argument.parse(arg)
            # Currently, we rely directly on the invariant that there are NO
            # kwarg-only mutating arguments.  If you want to relax this,
            # we will need a more semantic way of matching that takes
            # into account return arguments.  In that case, you will have
            # to manage out computation a level up, in FunctionSchema.  See Note
            # [is_out_fn]
            if parg.annotation is not None and parg.annotation.is_write:
                if arguments_acc is positional:
                    pass  # do nothing
                elif arguments_acc is kwarg_only:
                    arguments_acc = out
            else:
                if arguments_acc is out:
                    raise AssertionError(
                        f"non-mutable argument '{parg.name}' cannot follow mutable out arguments"
                    )
            arguments_acc.append(parg)

        return positional, kwarg_only, out