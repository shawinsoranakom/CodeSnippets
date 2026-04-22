def get_default_path_watcher_class() -> PathWatcherType:
    """Return the class to use for path changes notifications, based on the
    server.fileWatcherType config option.
    """
    return get_path_watcher_class(config.get_option("server.fileWatcherType"))