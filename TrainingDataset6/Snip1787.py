def _record_first_run():
    """Records shell pid to tracker file."""
    info = {'pid': _get_shell_pid(),
            'time': time.time()}

    mode = 'wb' if six.PY2 else 'w'
    with _get_not_configured_usage_tracker_path().open(mode) as tracker:
        json.dump(info, tracker)