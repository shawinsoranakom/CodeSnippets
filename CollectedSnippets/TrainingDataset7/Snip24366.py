def test_custom_srid(self):
        """Test with a null srid and a srid unknown to GDAL."""
        for srid in [None, 999999]:
            pnt = Point(111200, 220900, srid=srid)
            with self.subTest(srid=srid):
                self.assertTrue(
                    pnt.ewkt.startswith(
                        ("SRID=%s;" % srid if srid else "") + "POINT (111200"
                    )
                )
                self.assertIsInstance(pnt.ogr, gdal.OGRGeometry)
                self.assertIsNone(pnt.srs)

                # Test conversion from custom to a known srid
                c2w = gdal.CoordTransform(
                    gdal.SpatialReference(
                        "+proj=mill +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +R_A +datum=WGS84 "
                        "+units=m +no_defs"
                    ),
                    gdal.SpatialReference(4326),
                )
                new_pnt = pnt.transform(c2w, clone=True)
                self.assertEqual(new_pnt.srid, 4326)
                self.assertAlmostEqual(new_pnt.x, 1, 1)
                self.assertAlmostEqual(new_pnt.y, 2, 1)