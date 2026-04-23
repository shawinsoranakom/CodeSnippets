def main(arg_list: list[str] | None = None) -> int | str:
    args, help_text = _parse_args(arg_list)

    # Explicit arguments
    if args.choice:
        return choice(args.choice)

    if args.integer is not None:
        return randint(1, args.integer)

    if args.float is not None:
        return uniform(0, args.float)

    if args.test:
        _test(args.test)
        return ""

    # No explicit argument, select based on input
    if len(args.input) == 1:
        val = args.input[0]
        try:
            # Is it an integer?
            val = int(val)
            return randint(1, val)
        except ValueError:
            try:
                # Is it a float?
                val = float(val)
                return uniform(0, val)
            except ValueError:
                # Split in case of space-separated string: "a b c"
                return choice(val.split())

    if len(args.input) >= 2:
        return choice(args.input)

    return help_text