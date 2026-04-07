def _set_srs(self, srs):
        "Set the SpatialReference for this geometry."
        # Do not have to clone the `SpatialReference` object pointer because
        # when it is assigned to this `OGRGeometry` it's internal OGR
        # reference count is incremented, and will likewise be released
        # (decremented) when this geometry's destructor is called.
        if isinstance(srs, SpatialReference):
            srs_ptr = srs.ptr
        elif isinstance(srs, (int, str)):
            sr = SpatialReference(srs)
            srs_ptr = sr.ptr
        elif srs is None:
            srs_ptr = None
        else:
            raise TypeError(
                "Cannot assign spatial reference with object of type: %s" % type(srs)
            )
        capi.assign_srs(self.ptr, srs_ptr)