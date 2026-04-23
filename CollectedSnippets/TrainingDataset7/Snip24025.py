def test_multipoints(self):
        "Testing MultiPoint objects."
        for mp in self.geometries.multipoints:
            mgeom1 = OGRGeometry(mp.wkt)  # First one from WKT
            self.assertEqual(4, mgeom1.geom_type)
            self.assertEqual("MULTIPOINT", mgeom1.geom_name)
            mgeom2 = OGRGeometry("MULTIPOINT")  # Creating empty multipoint
            mgeom3 = OGRGeometry("MULTIPOINT")
            for g in mgeom1:
                mgeom2.add(g)  # adding each point from the multipoints
                mgeom3.add(g.wkt)  # should take WKT as well
            self.assertEqual(mgeom1, mgeom2)  # they should equal
            self.assertEqual(mgeom1, mgeom3)
            self.assertEqual(mp.coords, mgeom2.coords)
            self.assertEqual(mp.n_p, mgeom2.point_count)