def ellipsoid(self):
        """
        Return a tuple of the ellipsoid parameters:
         (semimajor axis, semiminor axis, and inverse flattening)
        """
        return (self.semi_major, self.semi_minor, self.inverse_flattening)