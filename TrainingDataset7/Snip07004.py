def _create_empty(cls):
        return capi.create_geom(OGRGeomType("point").num)