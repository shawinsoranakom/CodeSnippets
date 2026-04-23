def is_3d(self):
        """Return True if the geometry has Z coordinates."""
        return capi.is_3d(self.ptr)