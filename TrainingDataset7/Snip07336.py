def interpolate_normalized(self, distance):
        return self._topology(capi.geos_interpolate_normalized(self.ptr, distance))