def fromstr(string, **kwargs):
    "Given a string value, return a GEOSGeometry object."
    return GEOSGeometry(string, **kwargs)