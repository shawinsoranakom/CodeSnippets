def test05_geometries(self):
        "Testing Geometries from Data Source Features."
        for source in ds_list:
            ds = DataSource(source.ds)

            # Incrementing through each layer and feature.
            for layer in ds:
                geoms = layer.get_geoms()
                geos_geoms = layer.get_geoms(geos=True)
                self.assertEqual(len(geoms), len(geos_geoms))
                self.assertEqual(len(geoms), len(layer))
                for feat, geom, geos_geom in zip(layer, geoms, geos_geoms):
                    g = feat.geom
                    self.assertEqual(geom, g)
                    self.assertIsInstance(geos_geom, GEOSGeometry)
                    self.assertEqual(g, geos_geom.ogr)
                    # Making sure we get the right Geometry name & type
                    self.assertEqual(source.geom, g.geom_name)
                    self.assertEqual(source.gtype, g.geom_type)

                    # Making sure the SpatialReference is as expected.
                    if hasattr(source, "srs_wkt"):
                        self.assertIsNotNone(re.match(wgs_84_wkt_regex, g.srs.wkt))