def srs(self):
        """
        Return the SpatialReference used in this GDALRaster.
        """
        try:
            wkt = capi.get_ds_projection_ref(self._ptr)
            if not wkt:
                return None
            return SpatialReference(wkt, srs_type="wkt")
        except SRSException:
            return None