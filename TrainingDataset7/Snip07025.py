def add(self, geom):
        "Add the geometry to this Geometry Collection."
        if isinstance(geom, OGRGeometry):
            if isinstance(geom, self.__class__):
                for g in geom:
                    capi.add_geom(self.ptr, g.ptr)
            else:
                capi.add_geom(self.ptr, geom.ptr)
        elif isinstance(geom, str):
            tmp = OGRGeometry(geom)
            capi.add_geom(self.ptr, tmp.ptr)
        else:
            raise GDALException("Must add an OGRGeometry.")