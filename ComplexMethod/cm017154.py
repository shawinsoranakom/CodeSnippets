def test_mutable_geometries(self):
        "Testing the mutability of Polygons and Geometry Collections."
        # ### Testing the mutability of Polygons ###
        for p in self.geometries.polygons:
            poly = fromstr(p.wkt)
            msg = (
                "Parameter must be a sequence of LinearRings or objects that can "
                "initialize to LinearRings"
            )
            with self.subTest(p=p):
                # Should only be able to use __setitem__ with LinearRing
                # geometries.
                with self.assertRaisesMessage(TypeError, msg):
                    poly.__setitem__(0, LineString((1, 1), (2, 2)))

                # Construct the new shell by adding 500 to every point in the
                # old shell.
                shell_tup = poly.shell.tuple
                new_coords = []
                for point in shell_tup:
                    new_coords.append((point[0] + 500.0, point[1] + 500.0))
                new_shell = LinearRing(*tuple(new_coords))

                # Assigning polygon's exterior ring w/the new shell
                poly.exterior_ring = new_shell
                str(new_shell)  # new shell is still accessible
                self.assertEqual(poly.exterior_ring, new_shell)
                self.assertEqual(poly[0], new_shell)

        # ### Testing the mutability of Geometry Collections
        for tg in self.geometries.multipoints:
            mp = fromstr(tg.wkt)
            for i in range(len(mp)):
                # Creating a random point.
                pnt = mp[i]
                new = Point(random.randint(21, 100), random.randint(21, 100))
                with self.subTest(tg=tg, i=i):
                    # Testing the assignment
                    mp[i] = new
                    str(new)  # what was used for the assignment is still accessible
                    self.assertEqual(mp[i], new)
                    self.assertEqual(mp[i].wkt, new.wkt)
                    self.assertNotEqual(pnt, mp[i])

        # MultiPolygons involve much more memory management because each
        # Polygon w/in the collection has its own rings.
        for tg in self.geometries.multipolygons:
            mpoly = fromstr(tg.wkt)
            for i in range(len(mpoly)):
                poly = mpoly[i]
                old_poly = mpoly[i]
                # Offsetting the each ring in the polygon by 500.
                for j in range(len(poly)):
                    r = poly[j]
                    for k in range(len(r)):
                        r[k] = (r[k][0] + 500.0, r[k][1] + 500.0)
                    poly[j] = r

                with self.subTest(tg=tg, i=i, j=j):
                    self.assertNotEqual(mpoly[i], poly)
                    # Testing the assignment
                    mpoly[i] = poly
                    str(poly)  # Still accessible
                    self.assertEqual(mpoly[i], poly)
                    self.assertNotEqual(mpoly[i], old_poly)