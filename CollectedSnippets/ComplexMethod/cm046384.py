def print_args(args: dict | None = None, show_file=True, show_func=False):
    """Print function arguments (optional args dict).

    Args:
        args (dict, optional): Arguments to print.
        show_file (bool): Whether to show the file name.
        show_func (bool): Whether to show the function name.
    """

    def strip_auth(v):
        """Clean longer Ultralytics HUB URLs by stripping potential authentication information."""
        return clean_url(v) if (isinstance(v, str) and v.startswith("http") and len(v) > 100) else v

    x = inspect.currentframe().f_back  # previous frame
    file, _, func, _, _ = inspect.getframeinfo(x)
    if args is None:  # get args automatically
        args, _, _, frm = inspect.getargvalues(x)
        args = {k: v for k, v in frm.items() if k in args}
    try:
        file = Path(file).resolve().relative_to(ROOT).with_suffix("")
    except ValueError:
        file = Path(file).stem
    s = (f"{file}: " if show_file else "") + (f"{func}: " if show_func else "")
    LOGGER.info(colorstr(s) + ", ".join(f"{k}={strip_auth(v)}" for k, v in sorted(args.items())))