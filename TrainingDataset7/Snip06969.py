def _get_srs(self):
        "Return the Spatial Reference for this Geometry."
        try:
            srs_ptr = capi.get_geom_srs(self.ptr)
            return SpatialReference(srs_api.clone_srs(srs_ptr))
        except SRSException:
            return None