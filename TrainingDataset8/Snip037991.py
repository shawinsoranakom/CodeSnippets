def _get_arg_metadata(arg: object) -> Optional[str]:
    """Get metadata information related to the value of the given object."""
    with contextlib.suppress(Exception):
        if isinstance(arg, (bool)):
            return f"val:{arg}"

        if isinstance(arg, Sized):
            return f"len:{len(arg)}"

    return None