def _new_args_filter(cls, arg_sequence):
        """
        Generator filtering args.

        first standard filter, for cls.zero and cls.identity.
        Also reshape ``Max(a, Max(b, c))`` to ``Max(a, b, c)``,
        and check arguments for comparability
        """
        for arg in arg_sequence:
            # pre-filter, checking comparability of arguments
            if (
                not isinstance(arg, Expr)
                or arg.is_extended_real is False
                or (arg.is_number and not arg.is_comparable)
            ):
                raise ValueError(f"The argument '{arg}' is not comparable.")

            if arg == cls.zero:  # type: ignore[attr-defined]
                raise ShortCircuit(arg)
            elif arg == cls.identity:  # type: ignore[attr-defined]
                continue
            elif arg.func == cls:
                yield from arg.args
            else:
                yield arg