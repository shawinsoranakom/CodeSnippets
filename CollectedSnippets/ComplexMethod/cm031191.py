def _reset_tzpath(to=None, stacklevel=4):
    global TZPATH

    tzpaths = to
    if tzpaths is not None:
        if isinstance(tzpaths, (str, bytes)):
            raise TypeError(
                f"tzpaths must be a list or tuple, "
                + f"not {type(tzpaths)}: {tzpaths!r}"
            )

        tzpaths = [os.fspath(p) for p in tzpaths]
        if not all(isinstance(p, str) for p in tzpaths):
            raise TypeError(
                "All elements of a tzpath sequence must be strings or "
                "os.PathLike objects which convert to strings."
            )

        if not all(map(os.path.isabs, tzpaths)):
            raise ValueError(_get_invalid_paths_message(tzpaths))
        base_tzpath = tzpaths
    else:
        env_var = os.environ.get("PYTHONTZPATH", None)
        if env_var is None:
            env_var = sysconfig.get_config_var("TZPATH")
        base_tzpath = _parse_python_tzpath(env_var, stacklevel)

    TZPATH = tuple(base_tzpath)