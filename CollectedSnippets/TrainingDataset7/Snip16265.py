def make_aware_datetimes(dt, iana_key):
    """Makes one aware datetime for each supported time zone provider."""
    yield dt.replace(tzinfo=zoneinfo.ZoneInfo(iana_key))