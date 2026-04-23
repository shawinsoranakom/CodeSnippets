def print_args(args: dict | None = None, show_file=True, show_func=False):
    """Logs the arguments of the calling function, with options to include the filename and function name."""
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
    LOGGER.info(colorstr(s) + ", ".join(f"{k}={v}" for k, v in args.items()))