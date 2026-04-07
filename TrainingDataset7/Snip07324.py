def point_on_surface(self):
        "Compute an interior point of this Geometry."
        return self._topology(capi.geos_pointonsurface(self.ptr))