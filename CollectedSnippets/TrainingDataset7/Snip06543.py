def ellipsoid(self):
        """
        Return a tuple of the ellipsoid parameters:
        (semimajor axis, semiminor axis, and inverse flattening).
        """
        return self.srs.ellipsoid