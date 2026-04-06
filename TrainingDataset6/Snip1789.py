def _is_second_run():
    """Returns `True` when we know that `fuck` called second time."""
    tracker_path = _get_not_configured_usage_tracker_path()
    if not tracker_path.exists():
        return False

    current_pid = _get_shell_pid()
    with tracker_path.open('r') as tracker:
        try:
            info = json.load(tracker)
        except ValueError:
            return False

    if not (isinstance(info, dict) and info.get('pid') == current_pid):
        return False

    return (_get_previous_command() == 'fuck' or
            time.time() - info.get('time', 0) < const.CONFIGURATION_TIMEOUT)