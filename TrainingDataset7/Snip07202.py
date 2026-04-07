def _get_single_external(self, index):
        """
        Return the Geometry from this Collection at the given index (0-based).
        """
        # Checking the index and returning the corresponding GEOS geometry.
        return GEOSGeometry(
            capi.geom_clone(self._get_single_internal(index)), srid=self.srid
        )