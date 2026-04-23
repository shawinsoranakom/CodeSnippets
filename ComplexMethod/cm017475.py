def __set__(self, instance, value):
        """
        Retrieve the proxied geometry or raster with the corresponding class
        specified during initialization.

        To set geometries, use values of None, HEXEWKB, or WKT.
        To set rasters, use JSON or dict values.
        """
        # The geographic type of the field.
        gtype = self.field.geom_type

        if gtype == "RASTER" and (
            value is None or isinstance(value, (str, dict, self._klass))
        ):
            # For raster fields, ensure input is None or a string, dict, or
            # raster instance.
            pass
        elif isinstance(value, self._klass):
            # The geometry type must match that of the field -- unless the
            # general GeometryField is used.
            if value.srid is None:
                # Assigning the field SRID if the geometry has no SRID.
                value.srid = self.field.srid
        elif value is None or isinstance(value, (str, memoryview)):
            # Set geometries with None, WKT, HEX, or WKB
            pass
        else:
            raise TypeError(
                "Cannot set %s SpatialProxy (%s) with value of type: %s"
                % (instance.__class__.__name__, gtype, type(value))
            )

        # Setting the objects dictionary with the value, and returning.
        instance.__dict__[self.field.attname] = value
        return value