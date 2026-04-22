def get_path_watcher_class(watcher_type: str) -> PathWatcherType:
    """Return the PathWatcher class that corresponds to the given watcher_type
    string. Acceptable values are 'auto', 'watchdog', 'poll' and 'none'.
    """
    if watcher_type == "auto":
        if watchdog_available:
            return EventBasedPathWatcher
        else:
            return PollingPathWatcher
    elif watcher_type == "watchdog" and watchdog_available:
        return EventBasedPathWatcher
    elif watcher_type == "poll":
        return PollingPathWatcher
    else:
        return NoOpPathWatcher