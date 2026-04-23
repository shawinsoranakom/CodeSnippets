def get_app_template_dirs(dirname):
    """
    Return an iterable of paths of directories to load app templates from.

    dirname is the name of the subdirectory containing templates inside
    installed applications.
    """
    # Immutable return value because it will be cached and shared by callers.
    return tuple(
        path
        for app_config in apps.get_app_configs()
        if app_config.path and (path := Path(app_config.path) / dirname).is_dir()
    )