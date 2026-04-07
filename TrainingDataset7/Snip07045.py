def geom_type(self):
        "Return the geometry type (OGRGeomType) of the Layer."
        return OGRGeomType(capi.get_fd_geom_type(self._ldefn))