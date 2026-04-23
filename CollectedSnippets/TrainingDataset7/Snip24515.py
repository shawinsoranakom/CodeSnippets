def test_init(self):
        "Testing LayerMapping initialization."

        # Model field that does not exist.
        bad1 = copy(city_mapping)
        bad1["foobar"] = "FooField"

        # Shapefile field that does not exist.
        bad2 = copy(city_mapping)
        bad2["name"] = "Nombre"

        # Nonexistent geographic field type.
        bad3 = copy(city_mapping)
        bad3["point"] = "CURVE"

        # Incrementing through the bad mapping dictionaries and
        # ensuring that a LayerMapError is raised.
        for bad_map in (bad1, bad2, bad3):
            with self.assertRaises(LayerMapError):
                LayerMapping(City, city_shp, bad_map)

        # A LookupError should be thrown for bogus encodings.
        with self.assertRaises(LookupError):
            LayerMapping(City, city_shp, city_mapping, encoding="foobar")