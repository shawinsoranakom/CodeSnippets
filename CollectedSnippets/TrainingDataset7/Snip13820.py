def update_connections_time_zone(*, setting, **kwargs):
    if setting == "TIME_ZONE":
        # Reset process time zone
        if hasattr(time, "tzset"):
            if kwargs["value"]:
                os.environ["TZ"] = kwargs["value"]
            else:
                os.environ.pop("TZ", None)
            time.tzset()

        # Reset local time zone cache
        timezone.get_default_timezone.cache_clear()

    # Reset the database connections' time zone
    if setting in {"TIME_ZONE", "USE_TZ"}:
        for conn in connections.all(initialized_only=True):
            try:
                del conn.timezone
            except AttributeError:
                pass
            try:
                del conn.timezone_name
            except AttributeError:
                pass
            conn.ensure_timezone()