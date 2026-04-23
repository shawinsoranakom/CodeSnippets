def project(self, point):
        from .point import Point

        if not isinstance(point, Point):
            raise TypeError("locate_point argument must be a Point")
        return capi.geos_project(self.ptr, point.ptr)