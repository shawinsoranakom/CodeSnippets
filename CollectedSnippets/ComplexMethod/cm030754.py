def fromutc(self, dt):
        "datetime in UTC -> datetime in local time."

        if not isinstance(dt, datetime):
            raise TypeError("fromutc() requires a datetime argument")
        if dt.tzinfo is not self:
            raise ValueError("dt.tzinfo is not self")
        # Returned value satisfies
        #          dt + ldt.utcoffset() = ldt
        off0 = dt.replace(fold=0).utcoffset()
        off1 = dt.replace(fold=1).utcoffset()
        if off0 is None or off1 is None or dt.dst() is None:
            raise ValueError
        if off0 == off1:
            ldt = dt + off0
            off1 = ldt.utcoffset()
            if off0 == off1:
                return ldt
        # Now, we discovered both possible offsets, so
        # we can just try four possible solutions:
        for off in [off0, off1]:
            ldt = dt + off
            if ldt.utcoffset() == off:
                return ldt
            ldt = ldt.replace(fold=1)
            if ldt.utcoffset() == off:
                return ldt

        raise ValueError("No suitable local time found")