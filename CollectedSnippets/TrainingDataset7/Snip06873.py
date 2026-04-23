def deserialize(self, value):
        try:
            return GEOSGeometry(value)
        except (GEOSException, GDALException, ValueError, TypeError) as err:
            logger.error("Error creating geometry from value '%s' (%s)", value, err)
        return None