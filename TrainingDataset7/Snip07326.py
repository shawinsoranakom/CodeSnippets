def simplify(self, tolerance=0.0, preserve_topology=False):
        """
        Return the Geometry, simplified using the Douglas-Peucker algorithm
        to the specified tolerance (higher tolerance => less points). If no
        tolerance provided, defaults to 0.

        By default, don't preserve topology - e.g. polygons can be split,
        collapse to lines or disappear holes can be created or disappear, and
        lines can cross. By specifying preserve_topology=True, the result will
        have the same dimension and number of components as the input. This is
        significantly slower.
        """
        if preserve_topology:
            return self._topology(capi.geos_preservesimplify(self.ptr, tolerance))
        else:
            return self._topology(capi.geos_simplify(self.ptr, tolerance))