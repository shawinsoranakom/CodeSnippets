def all_locale_paths():
    """
    Return a list of paths to user-provides languages files.
    """
    globalpath = os.path.join(
        os.path.dirname(sys.modules[settings.__module__].__file__), "locale"
    )
    app_paths = []
    for app_config in apps.get_app_configs():
        locale_path = os.path.join(app_config.path, "locale")
        if os.path.exists(locale_path):
            app_paths.append(locale_path)
    return [globalpath, *settings.LOCALE_PATHS, *app_paths]