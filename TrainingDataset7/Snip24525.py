def test_textfield(self):
        "String content fits also in a TextField"
        mapping = copy(city_mapping)
        mapping["name_txt"] = "Name"
        lm = LayerMapping(City, city_shp, mapping)
        lm.save(silent=True, strict=True)
        self.assertEqual(City.objects.count(), 3)
        self.assertEqual(City.objects.get(name="Houston").name_txt, "Houston")