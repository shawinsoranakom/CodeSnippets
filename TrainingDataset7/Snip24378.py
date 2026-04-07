def test_collections_of_collections(self):
        "Testing GeometryCollection handling of other collections."
        # Creating a GeometryCollection WKT string composed of other
        # collections and polygons.
        coll = [mp.wkt for mp in self.geometries.multipolygons if mp.valid]
        coll.extend(mls.wkt for mls in self.geometries.multilinestrings)
        coll.extend(p.wkt for p in self.geometries.polygons)
        coll.extend(mp.wkt for mp in self.geometries.multipoints)
        gc_wkt = "GEOMETRYCOLLECTION(%s)" % ",".join(coll)

        # Should construct ok from WKT
        gc1 = GEOSGeometry(gc_wkt)

        # Should also construct ok from individual geometry arguments.
        gc2 = GeometryCollection(*tuple(g for g in gc1))

        # And, they should be equal.
        self.assertEqual(gc1, gc2)