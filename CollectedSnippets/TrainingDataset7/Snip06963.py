def set_3d(self, value):
        """Set if this geometry has Z coordinates."""
        if value is True:
            capi.set_3d(self.ptr, 1)
        elif value is False:
            capi.set_3d(self.ptr, 0)
        else:
            raise ValueError(f"Input to 'set_3d' must be a boolean, got '{value!r}'.")