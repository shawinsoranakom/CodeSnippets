def check_suffix(file="yolo26n.pt", suffix=".pt", msg=""):
    """Check file(s) for acceptable suffix.

    Args:
        file (str | list[str]): File or list of files to check.
        suffix (str | tuple): Acceptable suffix or tuple of suffixes.
        msg (str): Additional message to display in case of error.
    """
    if file and suffix:
        if isinstance(suffix, str):
            suffix = {suffix}
        for f in file if isinstance(file, (list, tuple)) else [file]:
            if s := str(f).rpartition(".")[-1].lower().strip():  # file suffix
                assert f".{s}" in suffix, f"{msg}{f} acceptable suffix is {suffix}, not .{s}"