def normalize(self, clone=False):
        """
        Convert this Geometry to normal form (or canonical form).
        If the `clone` keyword is set, then the geometry is not modified and a
        normalized clone of the geometry is returned instead.
        """
        if clone:
            clone = self.clone()
            capi.geos_normalize(clone.ptr)
            return clone
        capi.geos_normalize(self.ptr)