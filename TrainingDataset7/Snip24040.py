def test_add(self):
        "Testing GeometryCollection.add()."
        # Can't insert a Point into a MultiPolygon.
        mp = OGRGeometry("MultiPolygon")
        pnt = OGRGeometry("POINT(5 23)")
        with self.assertRaises(GDALException):
            mp.add(pnt)

        # GeometryCollection.add may take an OGRGeometry (if another collection
        # of the same type all child geoms will be added individually) or WKT.
        for mp in self.geometries.multipolygons:
            mpoly = OGRGeometry(mp.wkt)
            mp1 = OGRGeometry("MultiPolygon")
            mp2 = OGRGeometry("MultiPolygon")
            mp3 = OGRGeometry("MultiPolygon")

            for poly in mpoly:
                mp1.add(poly)  # Adding a geometry at a time
                mp2.add(poly.wkt)  # Adding WKT
            mp3.add(mpoly)  # Adding a MultiPolygon's entire contents at once.
            for tmp in (mp1, mp2, mp3):
                self.assertEqual(mpoly, tmp)