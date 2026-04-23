def test_emptyCollections(self):
        "Testing empty geometries and collections."
        geoms = [
            GeometryCollection([]),
            fromstr("GEOMETRYCOLLECTION EMPTY"),
            GeometryCollection(),
            fromstr("POINT EMPTY"),
            Point(),
            fromstr("LINESTRING EMPTY"),
            LineString(),
            fromstr("POLYGON EMPTY"),
            Polygon(),
            fromstr("MULTILINESTRING EMPTY"),
            MultiLineString(),
            fromstr("MULTIPOLYGON EMPTY"),
            MultiPolygon(()),
            MultiPolygon(),
        ]

        if numpy:
            geoms.append(LineString(numpy.array([])))

        for g in geoms:
            with self.subTest(g=g):
                self.assertIs(g.empty, True)

                # Testing len() and num_geom.
                if isinstance(g, Polygon):
                    self.assertEqual(1, len(g))  # Has one empty linear ring
                    self.assertEqual(1, g.num_geom)
                    self.assertEqual(0, len(g[0]))
                elif isinstance(g, (Point, LineString)):
                    self.assertEqual(1, g.num_geom)
                    self.assertEqual(0, len(g))
                else:
                    self.assertEqual(0, g.num_geom)
                    self.assertEqual(0, len(g))

                # Testing __getitem__ (doesn't work on Point or Polygon)
                if isinstance(g, Point):
                    msg = "Invalid GEOS Geometry index:"
                    with self.assertRaisesMessage(IndexError, msg):
                        g.x
                elif isinstance(g, Polygon):
                    lr = g.shell
                    self.assertEqual("LINEARRING EMPTY", lr.wkt)
                    self.assertEqual(0, len(lr))
                    self.assertIs(lr.empty, True)
                    msg = "invalid index: 0"
                    with self.assertRaisesMessage(IndexError, msg):
                        lr.__getitem__(0)
                else:
                    msg = "invalid index: 0"
                    with self.assertRaisesMessage(IndexError, msg):
                        g.__getitem__(0)