def errcheck(result, func, cargs):
        if not result:
            raise GEOSException(
                "Error encountered checking Coordinate Sequence returned from GEOS "
                'C function "%s".' % func.__name__
            )
        return result