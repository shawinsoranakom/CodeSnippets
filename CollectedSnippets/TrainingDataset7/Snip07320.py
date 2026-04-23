def convex_hull(self):
        """
        Return the smallest convex Polygon that contains all the points
        in the Geometry.
        """
        return self._topology(capi.geos_convexhull(self.ptr))