def _prepare_tzname_delta(self, tzname):
        tzname, sign, offset = split_tzname_delta(tzname)
        if offset:
            sign = "-" if sign == "+" else "+"
            return f"{tzname}{sign}{offset}"
        return tzname