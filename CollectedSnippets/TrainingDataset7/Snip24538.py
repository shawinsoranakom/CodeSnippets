def test_layermapping_default_db(self):
        lm = LayerMapping(City, city_shp, city_mapping)
        self.assertEqual(lm.using, "other")