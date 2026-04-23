def set_measured(self, value):
        """Set if this geometry has M coordinates."""
        if value is True:
            capi.set_measured(self.ptr, 1)
        elif value is False:
            capi.set_measured(self.ptr, 0)
        else:
            raise ValueError(
                f"Input to 'set_measured' must be a boolean, got '{value!r}'."
            )