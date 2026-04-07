def test_encoded_name(self):
        """Test a layer containing utf-8-encoded name"""
        city_shp = shp_path / "ch-city" / "ch-city.shp"
        lm = LayerMapping(City, city_shp, city_mapping)
        lm.save(silent=True, strict=True)
        self.assertEqual(City.objects.count(), 1)
        self.assertEqual(City.objects.all()[0].name, "Zürich")