def value(self):
        "Return a Python `datetime` object for this OFTDateTime field."
        # TODO: Adapt timezone information. See:
        #  https://lists.osgeo.org/pipermail/gdal-dev/2006-February/007990.html
        #  The `tz` variable has values of: 0=unknown, 1=localtime (ambiguous),
        #  100=GMT, 104=GMT+1, 80=GMT-5, etc.
        try:
            yy, mm, dd, hh, mn, ss, tz = self.as_datetime()
            return datetime(yy.value, mm.value, dd.value, hh.value, mn.value, ss.value)
        except (TypeError, ValueError, GDALException):
            return None