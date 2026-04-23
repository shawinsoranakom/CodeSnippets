def value(self):
        "Return a Python `time` object for this OFTTime field."
        try:
            yy, mm, dd, hh, mn, ss, tz = self.as_datetime()
            return time(hh.value, mn.value, ss.value)
        except (ValueError, GDALException):
            return None