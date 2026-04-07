def convex_hull(self):
        """
        Return the smallest convex Polygon that contains all the points in
        this Geometry.
        """
        return self._geomgen(capi.geom_convex_hull)