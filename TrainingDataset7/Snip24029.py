def test_polygons(self):
        "Testing Polygon objects."

        # Testing `from_bbox` class method
        bbox = (-180, -90, 180, 90)
        p = OGRGeometry.from_bbox(bbox)
        self.assertEqual(bbox, p.extent)

        prev = OGRGeometry("POINT(0 0)")
        for p in self.geometries.polygons:
            poly = OGRGeometry(p.wkt)
            self.assertEqual(3, poly.geom_type)
            self.assertEqual("POLYGON", poly.geom_name)
            self.assertEqual(p.n_p, poly.point_count)
            self.assertEqual(p.n_i + 1, len(poly))
            msg = "Index out of range when accessing rings of a polygon: %s."
            with self.assertRaisesMessage(IndexError, msg % len(poly)):
                poly.__getitem__(len(poly))

            # Testing area & centroid.
            self.assertAlmostEqual(p.area, poly.area, 9)
            x, y = poly.centroid.tuple
            self.assertAlmostEqual(p.centroid[0], x, 9)
            self.assertAlmostEqual(p.centroid[1], y, 9)

            # Testing equivalence
            self.assertEqual(poly, OGRGeometry(p.wkt))
            self.assertNotEqual(poly, prev)

            if p.ext_ring_cs:
                ring = poly[0]
                self.assertEqual(p.ext_ring_cs, ring.tuple)
                self.assertEqual(p.ext_ring_cs, poly[0].tuple)
                self.assertEqual(len(p.ext_ring_cs), ring.point_count)

            for r in poly:
                self.assertEqual("LINEARRING", r.geom_name)