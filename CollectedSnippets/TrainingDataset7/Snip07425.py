def _get_single_external(self, index):
        return GEOSGeometry(
            capi.geom_clone(self._get_single_internal(index)), srid=self.srid
        )