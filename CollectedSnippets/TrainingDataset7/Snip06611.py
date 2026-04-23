def unsupported_functions(self):
        unsupported = {
            "AsKML",
            "AsSVG",
            "Azimuth",
            "ClosestPoint",
            "ForcePolygonCW",
            "GeoHash",
            "GeometryDistance",
            "IsEmpty",
            "LineLocatePoint",
            "MakeValid",
            "MemSize",
            "NumDimensions",
            "Rotate",
            "Scale",
            "SnapToGrid",
            "Translate",
        }
        if self.connection.oracle_version < (23,):
            unsupported.add("GeometryType")
        return unsupported