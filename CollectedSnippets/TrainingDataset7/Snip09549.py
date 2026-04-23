def _prepare_tzname_delta(self, tzname):
        tzname, sign, offset = split_tzname_delta(tzname)
        return f"{sign}{offset}" if offset else tzname