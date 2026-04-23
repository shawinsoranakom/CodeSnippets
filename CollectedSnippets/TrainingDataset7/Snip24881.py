def now(cls, tz=None):
                if tz is None or tz.utcoffset(documented_now) is None:
                    return documented_now
                else:
                    return documented_now.replace(tzinfo=tz) + tz.utcoffset(now)