def test_polygons(self):
        "Testing Polygon objects."

        prev = fromstr("POINT(0 0)")
        for p in self.geometries.polygons:
            # Creating the Polygon, testing its properties.
            poly = fromstr(p.wkt)
            with self.subTest(p=p):
                self.assertEqual(poly.geom_type, "Polygon")
                self.assertEqual(poly.geom_typeid, 3)
                self.assertEqual(poly.dims, 2)
                self.assertIs(poly.empty, False)
                self.assertIs(poly.ring, False)
                self.assertEqual(p.n_i, poly.num_interior_rings)
                self.assertEqual(p.n_i + 1, len(poly))  # Testing __len__
                self.assertEqual(p.n_p, poly.num_points)

                # Area & Centroid
                self.assertAlmostEqual(p.area, poly.area, 9)
                self.assertAlmostEqual(p.centroid[0], poly.centroid.tuple[0], 9)
                self.assertAlmostEqual(p.centroid[1], poly.centroid.tuple[1], 9)

                # Testing the geometry equivalence
                self.assertEqual(poly, fromstr(p.wkt))
                # Should not be equal to previous geometry
                self.assertIs(poly == prev, False)  # Use assertIs() to test __eq__.
                self.assertIs(poly != prev, True)  # Use assertIs() to test __ne__.

                # Testing the exterior ring
                ring = poly.exterior_ring
                self.assertEqual(ring.geom_type, "LinearRing")
                self.assertEqual(ring.geom_typeid, 2)
                if p.ext_ring_cs:
                    self.assertEqual(p.ext_ring_cs, ring.tuple)
                    self.assertEqual(
                        p.ext_ring_cs, poly[0].tuple
                    )  # Testing __getitem__

                # Testing __getitem__ and __setitem__ on invalid indices
                poly_len = len(poly)
                msg = f"invalid index: {poly_len}"
                with self.assertRaisesMessage(IndexError, msg):
                    poly.__getitem__(poly_len)
                with self.assertRaisesMessage(IndexError, msg):
                    poly.__setitem__(poly_len, False)
                negative_index = -1 * poly_len - 1
                msg = f"invalid index: {negative_index}"
                with self.assertRaisesMessage(IndexError, msg):
                    poly.__getitem__(negative_index)

                # Testing __iter__
                for r in poly:
                    self.assertEqual(r.geom_type, "LinearRing")
                    self.assertEqual(r.geom_typeid, 2)

                # Testing polygon construction.
                msg = (
                    "Parameter must be a sequence of LinearRings or "
                    "objects that can initialize to LinearRings."
                )
                with self.assertRaisesMessage(TypeError, msg):
                    Polygon(0, [1, 2, 3])
                with self.assertRaisesMessage(TypeError, msg):
                    Polygon("foo")

                # Polygon(shell, (hole1, ... holeN))
                ext_ring, *int_rings = poly
                self.assertEqual(poly, Polygon(ext_ring, int_rings))

                # Polygon(shell_tuple, hole_tuple1, ... , hole_tupleN)
                ring_tuples = tuple(r.tuple for r in poly)
                self.assertEqual(poly, Polygon(*ring_tuples))

                # Constructing with tuples of LinearRings.
                self.assertEqual(poly.wkt, Polygon(*tuple(r for r in poly)).wkt)
                self.assertEqual(
                    poly.wkt, Polygon(*tuple(LinearRing(r.tuple) for r in poly)).wkt
                )