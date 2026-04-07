def test_data_source_str(self):
        lm = LayerMapping(City, str(city_shp), city_mapping)
        lm.save()
        self.assertEqual(City.objects.count(), 3)