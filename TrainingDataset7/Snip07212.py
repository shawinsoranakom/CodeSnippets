def _checkindex(self, index):
        "Check the given index."
        if not (0 <= index < self.size):
            raise IndexError(f"Invalid GEOS Geometry index: {index}")