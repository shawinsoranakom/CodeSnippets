def now(cls, tz=None):
        if tz is None or tz.utcoffset(now) is None:
            return now
        else:
            # equals now.replace(tzinfo=utc)
            return now.replace(tzinfo=tz) + tz.utcoffset(now)