def unsupported_functions(self):
        unsupported = {"GeometryDistance", "MemSize", "Rotate"}
        if not self.geom_lib_version():
            unsupported |= {"Azimuth", "GeoHash", "MakeValid"}
        if self.spatial_version < (5, 1):
            unsupported |= {"BoundingCircle"}
        return unsupported