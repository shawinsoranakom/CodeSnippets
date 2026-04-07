def prepared(self):
        """
        Return a PreparedGeometry corresponding to this geometry -- it is
        optimized for the contains, intersects, and covers operations.
        """
        return PreparedGeometry(self)