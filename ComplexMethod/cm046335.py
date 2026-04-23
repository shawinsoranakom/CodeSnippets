def merge_equals_args(args: list[str]) -> list[str]:
    """Merge arguments around isolated '=' in a list of strings and join fragments with brackets.

    This function handles the following cases:
        1. ['arg', '=', 'val'] becomes ['arg=val']
        2. ['arg=', 'val'] becomes ['arg=val']
        3. ['arg', '=val'] becomes ['arg=val']
        4. Joins fragments with brackets, e.g., ['imgsz=[3,', '640,', '640]'] becomes ['imgsz=[3,640,640]']

    Args:
        args (list[str]): A list of strings where each element represents an argument or fragment.

    Returns:
        (list[str]): A list of strings where the arguments around isolated '=' are merged and fragments with brackets
            are joined.

    Examples:
        >>> args = ["arg1", "=", "value", "arg2=", "value2", "arg3", "=value3", "imgsz=[3,", "640,", "640]"]
        >>> merge_equals_args(args)
        ['arg1=value', 'arg2=value2', 'arg3=value3', 'imgsz=[3,640,640]']
    """
    new_args = []
    current = ""
    depth = 0

    i = 0
    while i < len(args):
        arg = args[i]

        # Handle equals sign merging
        if arg == "=" and 0 < i < len(args) - 1:  # merge ['arg', '=', 'val']
            new_args[-1] += f"={args[i + 1]}"
            i += 2
            continue
        elif arg.endswith("=") and i < len(args) - 1 and "=" not in args[i + 1]:  # merge ['arg=', 'val']
            new_args.append(f"{arg}{args[i + 1]}")
            i += 2
            continue
        elif arg.startswith("=") and i > 0:  # merge ['arg', '=val']
            new_args[-1] += arg
            i += 1
            continue

        # Handle bracket joining
        depth += arg.count("[") - arg.count("]")
        current += arg
        if depth == 0:
            new_args.append(current)
            current = ""

        i += 1

    # Append any remaining current string
    if current:
        new_args.append(current)

    return new_args