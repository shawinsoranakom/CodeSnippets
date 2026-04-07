def test_get_units(self):
        epsg_4326 = next(f for f in test_srs if f["srid"] == 4326)
        unit, unit_name = self.SpatialRefSys().get_units(epsg_4326["wkt"])
        self.assertEqual(unit_name, "degree")
        self.assertAlmostEqual(unit, 0.01745329251994328)