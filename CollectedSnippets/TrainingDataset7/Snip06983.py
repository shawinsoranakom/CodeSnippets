def clone(self):
        "Clone this OGR Geometry."
        return OGRGeometry(capi.clone_geom(self.ptr), self.srs)