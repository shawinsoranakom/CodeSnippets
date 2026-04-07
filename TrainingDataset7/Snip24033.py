def test_srs(self):
        "Testing OGR Geometries with Spatial Reference objects."
        for mp in self.geometries.multipolygons:
            # Creating a geometry w/spatial reference
            sr = SpatialReference("WGS84")
            mpoly = OGRGeometry(mp.wkt, sr)
            self.assertEqual(sr.wkt, mpoly.srs.wkt)

            # Ensuring that SRS is propagated to clones.
            klone = mpoly.clone()
            self.assertEqual(sr.wkt, klone.srs.wkt)

            # Ensuring all children geometries (polygons and their rings) all
            # return the assigned spatial reference as well.
            for poly in mpoly:
                self.assertEqual(sr.wkt, poly.srs.wkt)
                for ring in poly:
                    self.assertEqual(sr.wkt, ring.srs.wkt)

            # Ensuring SRS propagate in topological ops.
            a = OGRGeometry(self.geometries.topology_geoms[0].wkt_a, sr)
            b = OGRGeometry(self.geometries.topology_geoms[0].wkt_b, sr)
            diff = a.difference(b)
            union = a.union(b)
            self.assertEqual(sr.wkt, diff.srs.wkt)
            self.assertEqual(sr.srid, union.srs.srid)

            # Instantiating w/an integer SRID
            mpoly = OGRGeometry(mp.wkt, 4326)
            self.assertEqual(4326, mpoly.srid)
            mpoly.srs = SpatialReference(4269)
            self.assertEqual(4269, mpoly.srid)
            self.assertEqual("NAD83", mpoly.srs.name)

            # Incrementing through the multipolygon after the spatial reference
            # has been re-assigned.
            for poly in mpoly:
                self.assertEqual(mpoly.srs.wkt, poly.srs.wkt)
                poly.srs = 32140
                for ring in poly:
                    # Changing each ring in the polygon
                    self.assertEqual(32140, ring.srs.srid)
                    self.assertEqual("NAD83 / Texas South Central", ring.srs.name)
                    ring.srs = str(SpatialReference(4326))  # back to WGS84
                    self.assertEqual(4326, ring.srs.srid)

                    # Using the `srid` property.
                    ring.srid = 4322
                    self.assertEqual("WGS 72", ring.srs.name)
                    self.assertEqual(4322, ring.srid)

            # srs/srid may be assigned their own values, even when srs is None.
            mpoly = OGRGeometry(mp.wkt, srs=None)
            mpoly.srs = mpoly.srs
            mpoly.srid = mpoly.srid