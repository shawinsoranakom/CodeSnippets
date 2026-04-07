def boundary(self):
        "Return the boundary of this geometry."
        return self._geomgen(capi.get_boundary)