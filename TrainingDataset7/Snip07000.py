def sym_difference(self, other):
        """
        Return a new geometry which is the symmetric difference of this
        geometry and the other.
        """
        return self._geomgen(capi.geom_sym_diff, other)