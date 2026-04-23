def file_path(file_path: str, filter_ext: tuple[str, ...] = ('',), env: Environment | None = None, *, check_exists: bool = True) -> str:
    """Verify that a file exists under a known `addons_path` directory and return its full path.

    Examples::

    >>> file_path('hr')
    >>> file_path('hr/static/description/icon.png')
    >>> file_path('hr/static/description/icon.png', filter_ext=('.png', '.jpg'))

    :param str file_path: absolute file path, or relative path within any `addons_path` directory
    :param list[str] filter_ext: optional list of supported extensions (lowercase, with leading dot)
    :param env: optional environment, required for a file path within a temporary directory
        created using `file_open_temporary_directory()`
    :param check_exists: check that the file exists (default: True)
    :return: the absolute path to the file
    :raise FileNotFoundError: if the file is not found under the known `addons_path` directories
    :raise ValueError: if the file doesn't have one of the supported extensions (`filter_ext`)
    """
    import odoo.addons  # noqa: PLC0415
    is_abs = os.path.isabs(file_path)
    normalized_path = os.path.normpath(os.path.normcase(file_path))

    if filter_ext and not normalized_path.lower().endswith(filter_ext):
        raise ValueError("Unsupported file: " + file_path)

    # ignore leading 'addons/' if present, it's the final component of root_path, but
    # may sometimes be included in relative paths
    normalized_path = normalized_path.removeprefix('addons' + os.sep)

    # if path is relative and represents a loaded module, accept only the
    # __path__ for that module; otherwise, search in all accepted paths
    file_path_split = normalized_path.split(os.path.sep)
    if not is_abs and (module := sys.modules.get(f'odoo.addons.{file_path_split[0]}')):
        addons_paths = list(map(os.path.dirname, module.__path__))
    else:
        root_path = os.path.abspath(config.root_path)
        temporary_paths = env.transaction._Transaction__file_open_tmp_paths if env else []
        addons_paths = [*odoo.addons.__path__, root_path, *temporary_paths]

    for addons_dir in addons_paths:
        # final path sep required to avoid partial match
        parent_path = os.path.normpath(os.path.normcase(addons_dir)) + os.sep
        if is_abs:
            fpath = normalized_path
        else:
            fpath = os.path.normpath(os.path.join(parent_path, normalized_path))
        if fpath.startswith(parent_path) and (
            # we check existence when asked or we have multiple paths to check
            # (there is one possibility for absolute paths)
            (not check_exists and (is_abs or len(addons_paths) == 1))
            or os.path.exists(fpath)
        ):
            return fpath

    raise FileNotFoundError("File not found: " + file_path)