def geom_type(self):
        "Return the OGR Geometry Type for this Feature."
        return OGRGeomType(capi.get_fd_geom_type(self._layer._ldefn))