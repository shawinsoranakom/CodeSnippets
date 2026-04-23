def assertSpatialIndexNotExists(self, table, column, raster=False):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        if raster:
            self.assertFalse(
                any(
                    "st_convexhull(%s)" % column in c["definition"]
                    for c in constraints.values()
                    if c["definition"] is not None
                )
            )
        else:
            self.assertNotIn([column], [c["columns"] for c in constraints.values()])