def test_coord_seq(self):
        "Testing Coordinate Sequence objects."
        for p in self.geometries.polygons:
            with self.subTest(p=p):
                if p.ext_ring_cs:
                    # Constructing the polygon and getting the coordinate
                    # sequence
                    poly = fromstr(p.wkt)
                    cs = poly.exterior_ring.coord_seq

                    self.assertEqual(
                        p.ext_ring_cs, cs.tuple
                    )  # done in the Polygon test too.
                    self.assertEqual(
                        len(p.ext_ring_cs), len(cs)
                    )  # Making sure __len__ works

                    # Checks __getitem__ and __setitem__
                    for expected_value, coord_sequence in zip(p.ext_ring_cs, cs):
                        self.assertEqual(expected_value, coord_sequence)

                        # Construct the test value to set the coordinate
                        # sequence with
                        if len(expected_value) == 2:
                            tset = (5, 23)
                        else:
                            tset = (5, 23, 8)
                        coord_sequence = tset

                        # Making sure every set point matches what we expect
                        self.assertEqual(tset, coord_sequence)