def _create_polygon(self, length, items):
        # Instantiate LinearRing objects if necessary, but don't clone them yet
        # _construct_ring will throw a TypeError if a parameter isn't a valid
        # ring If we cloned the pointers here, we wouldn't be able to clean up
        # in case of error.
        if not length:
            return capi.create_empty_polygon()

        rings = []
        for r in items:
            if isinstance(r, GEOM_PTR):
                rings.append(r)
            else:
                rings.append(self._construct_ring(r))

        shell = self._clone(rings.pop(0))

        n_holes = length - 1
        if n_holes:
            holes_param = (GEOM_PTR * n_holes)(*[self._clone(r) for r in rings])
        else:
            holes_param = None

        return capi.create_polygon(shell, holes_param, n_holes)