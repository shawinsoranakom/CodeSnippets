def unsupported_functions(self):
        unsupported = {
            "AsGML",
            "AsKML",
            "AsSVG",
            "Azimuth",
            "BoundingCircle",
            "ClosestPoint",
            "ForcePolygonCW",
            "GeometryDistance",
            "IsEmpty",
            "LineLocatePoint",
            "MakeValid",
            "MemSize",
            "NumDimensions",
            "Perimeter",
            "PointOnSurface",
            "Reverse",
            "Rotate",
            "Scale",
            "SnapToGrid",
            "Transform",
            "Translate",
        }
        if self.connection.mysql_is_mariadb:
            unsupported.remove("PointOnSurface")
            if self.connection.mysql_version < (12, 0, 1):
                unsupported.update({"GeoHash", "IsValid"})
        return unsupported