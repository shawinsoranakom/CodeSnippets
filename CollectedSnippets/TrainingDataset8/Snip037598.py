def _time_to_datetime(time_: time) -> datetime:
    # Note, here we pick an arbitrary date well after Unix epoch.
    # This prevents pre-epoch timezone issues (https://bugs.python.org/issue36759)
    # We're dropping the date from datetime later, anyway.
    return datetime.combine(date(2000, 1, 1), time_)