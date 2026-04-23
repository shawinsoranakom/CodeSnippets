def test_curved_geometries(self):
        for geom in self.geometries.curved_geoms:
            with self.subTest(wkt=geom.wkt, geom_name=geom.name):
                g = OGRGeometry(geom.wkt)
                self.assertEqual(geom.name, g.geom_type.name)
                self.assertEqual(geom.num, g.geom_type.num)
                msg = f"GEOS does not support {g.__class__.__qualname__}."
                with self.assertRaisesMessage(GEOSException, msg):
                    g.geos