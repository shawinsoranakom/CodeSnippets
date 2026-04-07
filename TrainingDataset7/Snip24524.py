def test_charfield_too_short(self):
        mapping = copy(city_mapping)
        mapping["name_short"] = "Name"
        lm = LayerMapping(City, city_shp, mapping)
        with self.assertRaises(InvalidString):
            lm.save(silent=True, strict=True)