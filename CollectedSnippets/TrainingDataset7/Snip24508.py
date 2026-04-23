def test_poly_multi(self):
        shp_file = os.path.join(TEST_DATA, "test_poly", "test_poly.shp")
        model_def = ogrinspect(shp_file, "MyModel", multi_geom=True)
        self.assertIn("geom = models.MultiPolygonField()", model_def)
        # Same test with a 25D-type geometry field
        shp_file = os.path.join(TEST_DATA, "gas_lines", "gas_leitung.shp")
        model_def = ogrinspect(shp_file, "MyModel", multi_geom=True)
        self.assertIn("geom = models.MultiLineStringField(srid=31253)", model_def)