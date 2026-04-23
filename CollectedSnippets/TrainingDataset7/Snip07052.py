def _set_spatial_filter(self, filter):
        if isinstance(filter, OGRGeometry):
            capi.set_spatial_filter(self.ptr, filter.ptr)
        elif isinstance(filter, (tuple, list)):
            if not len(filter) == 4:
                raise ValueError("Spatial filter list/tuple must have 4 elements.")
            # Map c_double onto params -- if a bad type is passed in it
            # will be caught here.
            xmin, ymin, xmax, ymax = map(c_double, filter)
            capi.set_spatial_filter_rect(self.ptr, xmin, ymin, xmax, ymax)
        elif filter is None:
            capi.set_spatial_filter(self.ptr, None)
        else:
            raise TypeError(
                "Spatial filter must be either an OGRGeometry instance, a 4-tuple, or "
                "None."
            )