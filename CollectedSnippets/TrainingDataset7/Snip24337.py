def test_points(self):
        "Testing Point objects."
        prev = fromstr("POINT(0 0)")
        for p in self.geometries.points:
            # Creating the point from the WKT
            pnt = fromstr(p.wkt)
            with self.subTest(p=p):
                self.assertEqual(pnt.geom_type, "Point")
                self.assertEqual(pnt.geom_typeid, 0)
                self.assertEqual(pnt.dims, 0)
                self.assertEqual(p.x, pnt.x)
                self.assertEqual(p.y, pnt.y)
                self.assertEqual(pnt, fromstr(p.wkt))
                self.assertIs(pnt == prev, False)  # Use assertIs() to test __eq__.

                # Making sure that the point's X, Y components are what we
                # expect
                self.assertAlmostEqual(p.x, pnt.tuple[0], 9)
                self.assertAlmostEqual(p.y, pnt.tuple[1], 9)

                # Testing the third dimension, and getting the tuple arguments
                if hasattr(p, "z"):
                    self.assertIs(pnt.hasz, True)
                    self.assertEqual(p.z, pnt.z)
                    self.assertEqual(p.z, pnt.tuple[2], 9)
                    tup_args = (p.x, p.y, p.z)
                    set_tup1 = (2.71, 3.14, 5.23)
                    set_tup2 = (5.23, 2.71, 3.14)
                else:
                    self.assertIs(pnt.hasz, False)
                    self.assertIsNone(pnt.z)
                    tup_args = (p.x, p.y)
                    set_tup1 = (2.71, 3.14)
                    set_tup2 = (3.14, 2.71)

                # Centroid operation on point should be point itself
                self.assertEqual(p.centroid, pnt.centroid.tuple)

                # Now testing the different constructors
                pnt2 = Point(tup_args)  # e.g., Point((1, 2))
                pnt3 = Point(*tup_args)  # e.g., Point(1, 2)
                self.assertEqual(pnt, pnt2)
                self.assertEqual(pnt, pnt3)

                # Now testing setting the x and y
                pnt.y = 3.14
                pnt.x = 2.71
                self.assertEqual(3.14, pnt.y)
                self.assertEqual(2.71, pnt.x)

                # Setting via the tuple/coords property
                pnt.tuple = set_tup1
                self.assertEqual(set_tup1, pnt.tuple)
                pnt.coords = set_tup2
                self.assertEqual(set_tup2, pnt.coords)

                prev = pnt