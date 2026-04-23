def project_normalized(self, point):
        from .point import Point

        if not isinstance(point, Point):
            raise TypeError("locate_point argument must be a Point")
        return capi.geos_project_normalized(self.ptr, point.ptr)