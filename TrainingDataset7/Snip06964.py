def is_measured(self):
        """Return True if the geometry has M coordinates."""
        return capi.is_measured(self.ptr)