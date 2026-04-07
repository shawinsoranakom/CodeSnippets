def check_geom(result, func, cargs):
    "Error checking on routines that return Geometries."
    if not result:
        raise GEOSException(
            'Error encountered checking Geometry returned from GEOS C function "%s".'
            % func.__name__
        )
    return result