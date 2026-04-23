def srs(self, value):
        """
        Set the spatial reference used in this GDALRaster. The input can be
        a SpatialReference or any parameter accepted by the SpatialReference
        constructor.
        """
        if isinstance(value, SpatialReference):
            srs = value
        elif isinstance(value, (int, str)):
            srs = SpatialReference(value)
        else:
            raise ValueError("Could not create a SpatialReference from input.")
        capi.set_ds_projection_ref(self._ptr, srs.wkt.encode())
        self._flush()