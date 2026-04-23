def filter_args(args: list[str], filters: dict[str, int]) -> list[str]:
    """Return a filtered version of the given command line arguments."""
    remaining = 0
    result = []
    pass_through_args: list[str] = []
    pass_through_explicit = False
    pass_through_implicit = False

    for arg in args:
        if pass_through_explicit:
            pass_through_args.append(arg)
            continue

        if arg == '--':
            pass_through_explicit = True
            continue

        if not arg.startswith('-') and remaining:
            remaining -= 1
            pass_through_implicit = not remaining
            continue

        if not arg.startswith('-') and pass_through_implicit:
            pass_through_args.append(arg)
            continue

        pass_through_implicit = False
        remaining = 0

        parts = arg.split('=', 1)
        key = parts[0]

        if key in filters:
            remaining = filters[key] - len(parts) + 1
            continue

        result.append(arg)

    if pass_through_args:
        result += ['--'] + pass_through_args

    return result