def value(self):
        "Return a Python `date` object for the OFTDate field."
        try:
            yy, mm, dd, hh, mn, ss, tz = self.as_datetime()
            return date(yy.value, mm.value, dd.value)
        except (TypeError, ValueError, GDALException):
            return None