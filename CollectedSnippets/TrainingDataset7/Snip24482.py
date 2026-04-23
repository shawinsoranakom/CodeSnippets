def assertSpatialIndexExists(self, table, column, raster=False):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        if raster:
            self.assertTrue(
                any(
                    "st_convexhull(%s)" % column in c["definition"]
                    for c in constraints.values()
                    if c["definition"] is not None
                )
            )
        else:
            self.assertIn([column], [c["columns"] for c in constraints.values()])