def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Include kwargs if they're not the default values.
        if self.dim != 2:
            kwargs["dim"] = self.dim
        if self.geography is not False:
            kwargs["geography"] = self.geography
        if self._extent != (-180.0, -90.0, 180.0, 90.0):
            kwargs["extent"] = self._extent
        if self._tolerance != 0.05:
            kwargs["tolerance"] = self._tolerance
        return name, path, args, kwargs