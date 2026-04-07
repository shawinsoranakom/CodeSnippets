def test_memory_hijinks(self):
        "Testing Geometry __del__() on rings and polygons."
        # #### Memory issues with rings and poly

        # These tests are needed to ensure sanity with writable geometries.

        # Getting a polygon with interior rings, and pulling out the interior
        # rings
        poly = fromstr(self.geometries.polygons[1].wkt)
        ring1 = poly[0]
        ring2 = poly[1]

        # These deletes should be 'harmless' since they are done on child
        # geometries
        del ring1
        del ring2
        ring1 = poly[0]
        ring2 = poly[1]

        # Deleting the polygon
        del poly

        # Access to these rings is OK since they are clones.
        str(ring1)
        str(ring2)