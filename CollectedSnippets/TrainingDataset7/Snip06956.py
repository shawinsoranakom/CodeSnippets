def geom_type(self):
        "Return the Type for this Geometry."
        return OGRGeomType(capi.get_geom_type(self.ptr))