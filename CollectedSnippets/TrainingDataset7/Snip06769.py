def get_prep_value(self, value):
        obj = super().get_prep_value(value)
        if obj is None:
            return None
        # When the input is not a geometry or raster, attempt to construct one
        # from the given string input.
        if isinstance(obj, GEOSGeometry):
            pass
        else:
            # Check if input is a candidate for conversion to raster or
            # geometry.
            is_candidate = isinstance(obj, (bytes, str)) or hasattr(
                obj, "__geo_interface__"
            )
            # Try to convert the input to raster.
            raster = self.get_raster_prep_value(obj, is_candidate)

            if raster:
                obj = raster
            elif is_candidate:
                try:
                    obj = GEOSGeometry(obj)
                except (GEOSException, GDALException):
                    raise ValueError(
                        "Couldn't create spatial object from lookup value '%s'." % obj
                    )
            else:
                raise ValueError(
                    "Cannot use object with type %s for a spatial lookup parameter."
                    % type(obj).__name__
                )

        # Assigning the SRID value.
        obj.srid = self.get_srid(obj)
        return obj