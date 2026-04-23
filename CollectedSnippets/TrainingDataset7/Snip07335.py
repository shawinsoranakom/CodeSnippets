def interpolate(self, distance):
        return self._topology(capi.geos_interpolate(self.ptr, distance))