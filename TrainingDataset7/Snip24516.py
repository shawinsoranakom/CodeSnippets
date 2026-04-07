def test_simple_layermap(self):
        "Test LayerMapping import of a simple point shapefile."
        # Setting up for the LayerMapping.
        lm = LayerMapping(City, city_shp, city_mapping)
        lm.save()

        # There should be three cities in the shape file.
        self.assertEqual(3, City.objects.count())

        # Opening up the shapefile, and verifying the values in each
        # of the features made it to the model.
        ds = DataSource(city_shp)
        layer = ds[0]
        for feat in layer:
            city = City.objects.get(name=feat["Name"].value)
            self.assertEqual(feat["Population"].value, city.population)
            self.assertEqual(Decimal(str(feat["Density"])), city.density)
            self.assertEqual(feat["Created"].value, city.dt)

            # Comparing the geometries.
            pnt1, pnt2 = feat.geom, city.point
            self.assertAlmostEqual(pnt1.x, pnt2.x, 5)
            self.assertAlmostEqual(pnt1.y, pnt2.y, 5)