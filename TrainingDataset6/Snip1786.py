def _get_not_configured_usage_tracker_path():
    """Returns path of special file where we store latest shell pid."""
    return Path(gettempdir()).joinpath(u'thefuck.last_not_configured_run_{}'.format(
        getpass.getuser(),
    ))