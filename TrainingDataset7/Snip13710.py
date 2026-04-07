def parallel_type(value):
    """Parse value passed to the --parallel option."""
    if value == "auto":
        return value
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not an integer or the string 'auto'"
        )